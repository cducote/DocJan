"""
FastAPI server to expose Concatly functionality as REST APIs
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import asyncio
from datetime import datetime
import json

# Fix for SQLite3 version compatibility
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from config.settings import validate_config
from models.database import get_document_database
from confluence.api import ConfluenceAPI
from ai.merging import merge_duplicates

app = FastAPI(title="Concatly API", version="1.0.0")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ConnectionStatus(BaseModel):
    status: str
    confluence_connected: bool
    database_connected: bool
    vector_store_ready: bool
    last_sync: Optional[datetime] = None
    document_count: Optional[int] = None

class SyncRequest(BaseModel):
    organization_id: str
    confluence_url: str
    username: str
    api_token: str

# Global state (in production, use Redis or database)
sync_status = {}

@app.get("/")
async def root():
    return {"message": "Concatly API is running"}

@app.get("/health")
async def health_check():
    try:
        validate_config()
        db = get_document_database()
        return {
            "status": "healthy",
            "database": "connected" if db else "disconnected",
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{organization_id}", response_model=ConnectionStatus)
async def get_connection_status(organization_id: str):
    """Get the connection and sync status for an organization"""
    try:
        # Check if we have sync status for this org
        org_status = sync_status.get(organization_id, {})
        
        # Check database connection
        db = get_document_database()
        db_connected = db is not None
        
        # Check if vector store has documents
        vector_ready = False
        doc_count = 0
        
        if db_connected:
            try:
                # Simple query to check if we have documents
                # You can adapt this based on your actual database schema
                doc_count = len(db.get_all_documents()) if hasattr(db, 'get_all_documents') else 0
                vector_ready = doc_count > 0
            except:
                vector_ready = False
        
        return ConnectionStatus(
            status=org_status.get("status", "not_connected"),
            confluence_connected=org_status.get("confluence_connected", False),
            database_connected=db_connected,
            vector_store_ready=vector_ready,
            last_sync=org_status.get("last_sync"),
            document_count=doc_count
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/{organization_id}")
async def start_sync(organization_id: str, sync_request: SyncRequest, background_tasks: BackgroundTasks):
    """Start syncing Confluence data for an organization"""
    
    # Set initial status
    sync_status[organization_id] = {
        "status": "syncing",
        "confluence_connected": False,
        "last_sync": datetime.now()
    }
    
    # Run sync in background
    background_tasks.add_task(run_sync, organization_id, sync_request)
    
    return {"message": "Sync started", "organization_id": organization_id}

async def run_sync(organization_id: str, sync_request: SyncRequest):
    """Background task to sync Confluence data"""
    try:
        # Update environment for this sync
        os.environ["CONFLUENCE_BASE_URL"] = sync_request.confluence_url
        os.environ["CONFLUENCE_USERNAME"] = sync_request.username
        os.environ["CONFLUENCE_API_TOKEN"] = sync_request.api_token
        
        # Test Confluence connection
        confluence_api = ConfluenceAPI()
        spaces = confluence_api.get_spaces()
        
        sync_status[organization_id]["confluence_connected"] = True
        sync_status[organization_id]["status"] = "indexing"
        
        # Here you would run your existing vectorization logic
        # For now, simulate the process
        await asyncio.sleep(2)  # Simulate processing time
        
        sync_status[organization_id]["status"] = "completed"
        sync_status[organization_id]["last_sync"] = datetime.now()
        
    except Exception as e:
        sync_status[organization_id]["status"] = "error"
        sync_status[organization_id]["error"] = str(e)

@app.get("/duplicates/{organization_id}")
async def get_duplicates(organization_id: str):
    """Get duplicate detection results"""
    try:
        # Here you would call your existing duplicate detection logic
        # For now, return mock data
        return {
            "duplicates_found": 5,
            "spaces_analyzed": ["DEV", "PROD", "DOCS"],
            "last_analysis": datetime.now(),
            "duplicates": [
                {
                    "id": "dup_1",
                    "title": "API Documentation",
                    "similarity": 0.95,
                    "pages": [
                        {"id": "page_1", "title": "API Docs v1", "space": "DEV"},
                        {"id": "page_2", "title": "API Documentation", "space": "PROD"}
                    ]
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
