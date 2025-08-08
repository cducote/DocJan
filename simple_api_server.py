"""
Simple FastAPI server for Concatly - provides status and sync endpoints
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime

app = FastAPI(title="Concatly API", version="1.0.0")

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for demo (in production, use a database)
organization_status = {}
sync_tasks = {}

class SyncRequest(BaseModel):
    organization_id: str
    confluence_url: str
    username: str
    api_token: str

class ConnectionStatus(BaseModel):
    status: str
    confluence_connected: bool
    database_connected: bool
    vector_store_ready: bool
    last_sync: Optional[str] = None
    document_count: Optional[int] = None

@app.get("/")
async def root():
    return {"message": "Concatly API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status/{organization_id}")
async def get_connection_status(organization_id: str) -> ConnectionStatus:
    """Get the connection and setup status for an organization"""
    
    # Check if we have any stored status for this organization
    if organization_id in organization_status:
        stored_status = organization_status[organization_id]
        return ConnectionStatus(**stored_status)
    
    # Default status for new organizations
    return ConnectionStatus(
        status="not_configured",
        confluence_connected=False,
        database_connected=False,
        vector_store_ready=False,
        last_sync=None,
        document_count=None
    )

@app.post("/sync/{organization_id}")
async def start_sync(organization_id: str, sync_request: SyncRequest, background_tasks: BackgroundTasks):
    """Start data sync process for an organization"""
    
    # Validate the sync request
    if not all([sync_request.confluence_url, sync_request.username, sync_request.api_token]):
        raise HTTPException(status_code=400, detail="Missing required Confluence credentials")
    
    # Test Confluence connection (simplified)
    confluence_connected = test_confluence_connection(
        sync_request.confluence_url, 
        sync_request.username, 
        sync_request.api_token
    )
    
    if not confluence_connected:
        raise HTTPException(status_code=400, detail="Could not connect to Confluence with provided credentials")
    
    # Update organization status to show sync in progress
    organization_status[organization_id] = {
        "status": "syncing",
        "confluence_connected": True,
        "database_connected": True,  # Assume database is always available
        "vector_store_ready": False,
        "last_sync": datetime.now().isoformat(),
        "document_count": None
    }
    
    # Start background sync task
    background_tasks.add_task(perform_sync, organization_id, sync_request)
    
    return {"message": "Sync started", "organization_id": organization_id}

@app.get("/duplicates/{organization_id}")
async def get_duplicates(organization_id: str):
    """Get detected duplicates for an organization"""
    
    # Check if vector store is ready
    status = await get_connection_status(organization_id)
    if not status.vector_store_ready:
        raise HTTPException(status_code=400, detail="Vector store not ready. Complete initial sync first.")
    
    # Return mock duplicate data for now
    return {
        "duplicate_pairs": [
            {
                "id": 1,
                "page1": {"title": "Getting Started Guide", "url": "https://example.com/page1"},
                "page2": {"title": "Quick Start Tutorial", "url": "https://example.com/page2"},
                "similarity": 0.87,
                "status": "pending"
            },
            {
                "id": 2,
                "page1": {"title": "API Documentation", "url": "https://example.com/page3"},
                "page2": {"title": "API Reference", "url": "https://example.com/page4"},
                "similarity": 0.92,
                "status": "pending"
            }
        ],
        "total_pairs": 2,
        "total_documents": 156,
        "documents_with_duplicates": 4
    }

def test_confluence_connection(confluence_url: str, username: str, api_token: str) -> bool:
    """Test if we can connect to Confluence with the provided credentials"""
    try:
        import requests
        
        # Simple test - try to get user info
        test_url = f"{confluence_url}/rest/api/user/current"
        response = requests.get(
            test_url,
            auth=(username, api_token),
            timeout=10
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"Confluence connection test failed: {e}")
        return False

async def perform_sync(organization_id: str, sync_request: SyncRequest):
    """Background task to perform the actual sync"""
    try:
        print(f"Starting sync for organization {organization_id}")
        
        # Simulate sync process
        import asyncio
        await asyncio.sleep(5)  # Simulate processing time
        
        # Update status to complete
        organization_status[organization_id] = {
            "status": "ready",
            "confluence_connected": True,
            "database_connected": True,
            "vector_store_ready": True,
            "last_sync": datetime.now().isoformat(),
            "document_count": 156  # Mock document count
        }
        
        print(f"Sync completed for organization {organization_id}")
        
    except Exception as e:
        print(f"Sync failed for organization {organization_id}: {e}")
        
        # Update status to show error
        organization_status[organization_id] = {
            "status": "error",
            "confluence_connected": False,
            "database_connected": True,
            "vector_store_ready": False,
            "last_sync": datetime.now().isoformat(),
            "document_count": None
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
