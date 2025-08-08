"""
Enhanced FastAPI server for Concatly - integrates real data ingestion from Streamlit app
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import asyncio
from datetime import datetime

# Fix for SQLite3 version compatibility
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

app = FastAPI(title="Concatly API", version="1.0.0")

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for organization status
organization_status = {}
sync_tasks = {}
# Cache for duplicate data to avoid recalculating
duplicate_cache = {}

class SyncRequest(BaseModel):
    organization_id: str
    confluence_url: str
    username: str
    api_token: str
    selected_spaces: Optional[List[str]] = ["SD"]  # Default spaces to sync

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
    
    # Check if we already have documents in the vector store
    try:
        from models.database import get_document_database
        db = get_document_database()
        all_docs = db.get()
        
        if all_docs['documents'] and len(all_docs['documents']) > 0:
            # We have documents, so system was previously set up
            return ConnectionStatus(
                status="ready",
                confluence_connected=True,
                database_connected=True,
                vector_store_ready=True,
                last_sync=None,  # Could track this in the future
                document_count=len(all_docs['documents'])
            )
    except Exception as e:
        print(f"Error checking existing documents: {e}")
    
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
    
    # Test Confluence connection
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
        "database_connected": True,
        "vector_store_ready": False,
        "last_sync": datetime.now().isoformat(),
        "document_count": None
    }
    
    # Start background sync task
    background_tasks.add_task(perform_real_sync, organization_id, sync_request)
    
    return {"message": "Sync started", "organization_id": organization_id}

@app.get("/duplicates/{organization_id}")
async def get_duplicates(organization_id: str):
    """Get detected duplicates for an organization"""
    
    # Check if vector store is ready
    status = await get_connection_status(organization_id)
    if not status.vector_store_ready:
        raise HTTPException(status_code=400, detail="Vector store not ready. Complete initial sync first.")
    
    # Check cache first for faster response
    cache_key = f"{organization_id}_duplicates"
    if cache_key in duplicate_cache:
        print(f"Returning cached duplicate data for {organization_id}")
        return duplicate_cache[cache_key]
    
    print(f"Computing duplicate data for {organization_id} (not cached)")
    
    # Get real duplicate data using the original Streamlit logic
    try:
        # Import required modules
        from models.database import get_document_database
        
        # Get all documents from ChromaDB directly to avoid Streamlit dependencies
        db = get_document_database()
        all_docs = db.get()
        
        if not all_docs['documents']:
            return {
                "duplicate_pairs": [],
                "total_pairs": 0,
                "total_documents": 0,
                "documents_with_duplicates": 0
            }
        
        duplicate_pairs = []
        processed_pairs = set()
        
        for i, metadata in enumerate(all_docs['metadatas']):
            similar_docs_str = metadata.get('similar_docs', '')
            
            if not similar_docs_str:
                continue
            
            similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
            
            for similar_id in similar_doc_ids:
                # Find the similar document
                similar_idx = None
                for j, other_metadata in enumerate(all_docs['metadatas']):
                    if other_metadata.get('doc_id', f'doc_{j}') == similar_id:
                        similar_idx = j
                        break
                
                if similar_idx is None:
                    continue
                
                # Create a unique pair identifier to avoid duplicates
                doc1_id = metadata.get('doc_id', f'doc_{i}')
                doc2_id = similar_id
                pair_key = tuple(sorted([doc1_id, doc2_id]))
                
                if pair_key in processed_pairs:
                    continue
                
                processed_pairs.add(pair_key)
                
                # Create document objects with metadata (avoiding Streamlit dependencies)
                doc1_metadata = metadata.copy()
                doc2_metadata = all_docs['metadatas'][similar_idx].copy()
                
                # Use space_key as space_name if space_name is not available
                if 'space_name' not in doc1_metadata:
                    doc1_metadata['space_name'] = doc1_metadata.get('space_key', 'Unknown')
                if 'space_name' not in doc2_metadata:
                    doc2_metadata['space_name'] = doc2_metadata.get('space_key', 'Unknown')
                
                # Create document-like objects
                doc1 = {
                    'page_content': all_docs['documents'][i],
                    'metadata': doc1_metadata
                }
                
                doc2 = {
                    'page_content': all_docs['documents'][similar_idx],
                    'metadata': doc2_metadata
                }
                
                # Use pre-computed similarity or calculate from stored embeddings
                try:
                    # First try to get similarity from metadata if available
                    similarity = doc1_metadata.get('similarity_score')
                    if similarity is None:
                        # Fall back to using stored embeddings from ChromaDB (much faster than re-generating)
                        from sklearn.metrics.pairwise import cosine_similarity
                        
                        # Get the stored embeddings from ChromaDB
                        embedding1 = all_docs['embeddings'][i] if all_docs.get('embeddings') else None
                        embedding2 = all_docs['embeddings'][similar_idx] if all_docs.get('embeddings') else None
                        
                        if embedding1 and embedding2:
                            # Calculate cosine similarity using stored embeddings
                            similarity_matrix = cosine_similarity([embedding1], [embedding2])
                            similarity = float(similarity_matrix[0][0])
                        else:
                            # Fall back to a reasonable default if embeddings not available
                            similarity = 0.75
                    
                except Exception as e:
                    print(f"Warning: Could not calculate similarity for pair {doc1_id}-{doc2_id}: {e}")
                    # Fall back to a reasonable default
                    similarity = 0.75
                
                duplicate_pairs.append({
                    'doc1': doc1,
                    'doc2': doc2,
                    'similarity': similarity,
                    'doc1_id': doc1_id,
                    'doc2_id': doc2_id
                })
        
        # Format for API response
        formatted_pairs = []
        
        for pair in duplicate_pairs:
            formatted_pairs.append({
                "id": len(formatted_pairs) + 1,
                "page1": {
                    "title": pair['doc1']['metadata'].get('title', 'Unknown'),
                    "url": pair['doc1']['metadata'].get('source', ''),
                    "space": pair['doc1']['metadata'].get('space_name', pair['doc1']['metadata'].get('space_key', 'Unknown'))
                },
                "page2": {
                    "title": pair['doc2']['metadata'].get('title', 'Unknown'), 
                    "url": pair['doc2']['metadata'].get('source', ''),
                    "space": pair['doc2']['metadata'].get('space_name', pair['doc2']['metadata'].get('space_key', 'Unknown'))
                },
                "similarity": round(pair.get('similarity', 0.75), 3),
                "status": "pending"
            })
        
        # Calculate stats
        total_docs = len(all_docs['documents'])
        unique_docs = set()
        for pair in duplicate_pairs:
            unique_docs.add(pair['doc1_id'])
            unique_docs.add(pair['doc2_id'])
        
        result = {
            "duplicate_pairs": formatted_pairs,
            "total_pairs": len(formatted_pairs),
            "total_documents": total_docs,
            "documents_with_duplicates": len(unique_docs)
        }
        
        # Cache the result for faster subsequent loads
        duplicate_cache[cache_key] = result
        print(f"Cached duplicate data for {organization_id}")
        
        return result
        
    except Exception as e:
        print(f"Error getting duplicates: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving duplicate data")

def test_confluence_connection(confluence_url: str, username: str, api_token: str) -> bool:
    """Test if we can connect to Confluence with the provided credentials"""
    try:
        import requests
        
        # Set up configuration temporarily for the test
        os.environ['CONFLUENCE_BASE_URL'] = confluence_url
        os.environ['CONFLUENCE_USERNAME'] = username  
        os.environ['CONFLUENCE_API_TOKEN'] = api_token
        
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

def get_space_name_from_confluence(space_key: str, confluence_url: str, username: str, api_token: str) -> str:
    """Get space name from Confluence API using space key"""
    try:
        import requests
        
        if not space_key or space_key == 'Unknown':
            return 'Unknown Space'
        
        # Get space info from Confluence API
        space_url = f"{confluence_url}/rest/api/space/{space_key}"
        response = requests.get(
            space_url,
            auth=(username, api_token),
            timeout=10
        )
        
        if response.status_code == 200:
            space_data = response.json()
            return space_data.get('name', space_key)
        else:
            print(f"Failed to get space name for {space_key}: {response.status_code}")
            return space_key
            
    except Exception as e:
        print(f"Error getting space name for {space_key}: {e}")
        return space_key

async def perform_real_sync(organization_id: str, sync_request: SyncRequest):
    """Background task to perform the actual document ingestion using original Streamlit logic"""
    try:
        print(f"Starting real sync for organization {organization_id}")
        
        # Set up environment variables for the sync
        os.environ['CONFLUENCE_BASE_URL'] = sync_request.confluence_url
        os.environ['CONFLUENCE_USERNAME'] = sync_request.username
        os.environ['CONFLUENCE_API_TOKEN'] = sync_request.api_token
        
        # Use the original Confluence API loading logic
        from confluence.api import load_documents_from_spaces
        
        # Load documents from selected spaces (default to SD if not specified)
        spaces_to_sync = sync_request.selected_spaces or ["SD"]
        print(f"Loading documents from spaces: {spaces_to_sync}")
        
        # Perform the actual document loading
        result = load_documents_from_spaces(spaces_to_sync, limit_per_space=100)
        
        if result['success']:
            print(f"Successfully loaded {result['total_loaded']} documents")
            
            # Update status to complete
            organization_status[organization_id] = {
                "status": "ready",
                "confluence_connected": True,
                "database_connected": True,
                "vector_store_ready": True,
                "last_sync": datetime.now().isoformat(),
                "document_count": result['total_loaded']
            }
            
            print(f"Sync completed for organization {organization_id}")
        else:
            print(f"Sync failed: {result['message']}")
            raise Exception(result['message'])
            
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
