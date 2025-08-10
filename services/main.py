"""
FastAPI Application for Confluence Document Processing Service.
Clean, containerized backend for connecting to Confluence, processing documents, and managing vector embeddings.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our service modules
from confluence_service import ConfluenceService, ConfluenceConfig
from vector_store_service import VectorStoreService, VectorStoreConfig

# Initialize FastAPI app
app = FastAPI(
    title="Confluence Document Processing API",
    description="Containerized service for Confluence document ingestion, vectorization, and duplicate detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances (will be initialized on startup)
confluence_service: Optional[ConfluenceService] = None
vector_store_service: Optional[VectorStoreService] = None

# In-memory status tracking
processing_status = {}


# Pydantic models
class ConfluenceCredentials(BaseModel):
    """Confluence connection credentials."""
    base_url: str = Field(..., description="Confluence base URL")
    username: str = Field(..., description="Confluence username/email")
    api_token: str = Field(..., description="Confluence API token")


class ProcessingRequest(BaseModel):
    """Request to process documents from Confluence spaces."""
    credentials: ConfluenceCredentials
    space_keys: List[str] = Field(..., description="List of space keys to process")
    limit_per_space: Optional[int] = Field(None, description="Optional limit per space")
    similarity_threshold: float = Field(0.65, description="Threshold for duplicate detection")


class ConnectionStatus(BaseModel):
    """Connection and processing status."""
    confluence_connected: bool
    vector_store_connected: bool
    document_count: int
    last_processed: Optional[str] = None
    status: str


class SpaceInfo(BaseModel):
    """Confluence space information."""
    key: str
    name: str
    type: str
    description: str


class DuplicatePair(BaseModel):
    """Duplicate document pair."""
    id: int
    page1: Dict[str, str]
    page2: Dict[str, str]
    similarity: float
    status: str


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global vector_store_service
    
    try:
        # Initialize vector store service from environment
        vector_store_service = VectorStoreConfig.create_service_from_env()
        print("✅ Vector store service initialized successfully")
    except Exception as e:
        print(f"⚠️ Vector store service initialization failed: {e}")
        # Continue without vector store - will be initialized on first request


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "vector_store": vector_store_service is not None,
            "confluence": confluence_service is not None
        }
    }


# Connection test endpoint
@app.post("/test-connection")
async def test_connection(credentials: ConfluenceCredentials):
    """Test connection to Confluence with provided credentials."""
    try:
        # Create temporary Confluence service for testing
        confluence = ConfluenceService(
            base_url=credentials.base_url,
            username=credentials.username,
            api_token=credentials.api_token
        )
        
        # Test connection
        success, message = confluence.test_connection()
        
        if not success:
            raise HTTPException(status_code=401, detail=message)
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


# Get available spaces
@app.post("/spaces")
async def get_spaces(credentials: ConfluenceCredentials) -> List[SpaceInfo]:
    """Get all accessible Confluence spaces."""
    try:
        # Create Confluence service
        confluence = ConfluenceService(
            base_url=credentials.base_url,
            username=credentials.username,
            api_token=credentials.api_token
        )
        
        # Get spaces
        success, spaces, message = confluence.get_all_accessible_spaces()
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return [SpaceInfo(**space) for space in spaces]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch spaces: {str(e)}")


# Process documents endpoint
@app.post("/process")
async def process_documents(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Start document processing from Confluence spaces."""
    try:
        # Generate processing ID
        processing_id = f"proc_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Initialize status
        processing_status[processing_id] = {
            "status": "starting",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "spaces": request.space_keys,
            "documents_loaded": 0,
            "duplicates_found": 0,
            "message": "Processing started"
        }
        
        # Start background processing
        background_tasks.add_task(
            process_documents_background,
            processing_id,
            request
        )
        
        return {
            "processing_id": processing_id,
            "status": "started",
            "message": f"Document processing started for {len(request.space_keys)} spaces"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


# Get processing status
@app.get("/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """Get status of a processing job."""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    return processing_status[processing_id]


# Get connection status
@app.get("/connection-status")
async def get_connection_status() -> ConnectionStatus:
    """Get overall connection and system status."""
    try:
        # Check vector store
        vector_store_connected = False
        document_count = 0
        
        if vector_store_service:
            vs_success, vs_message = vector_store_service.test_connection()
            vector_store_connected = vs_success
            if vs_success:
                document_count = vector_store_service.get_document_count()
        
        # Determine overall status
        if vector_store_connected:
            if document_count > 0:
                status = "ready"
            else:
                status = "connected_no_data"
        else:
            status = "not_configured"
        
        return ConnectionStatus(
            confluence_connected=confluence_service is not None,
            vector_store_connected=vector_store_connected,
            document_count=document_count,
            status=status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


# Get duplicates
@app.get("/duplicates")
async def get_duplicates() -> List[DuplicatePair]:
    """Get all detected duplicate document pairs."""
    try:
        global vector_store_service
        
        if not vector_store_service:
            raise HTTPException(status_code=400, detail="Vector store not initialized")
        
        duplicates = vector_store_service.get_duplicates()
        return [DuplicatePair(**dup) for dup in duplicates]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get duplicates: {str(e)}")


# Get duplicate summary (fast, just counts)
@app.get("/duplicates/summary")
async def get_duplicate_summary():
    """Get duplicate summary without expensive calculations."""
    try:
        global vector_store_service
        
        if not vector_store_service:
            raise HTTPException(status_code=400, detail="Vector store not initialized")
        
        # Get basic document count
        document_count = vector_store_service.get_document_count()
        
        # Count documents that have similar_docs metadata (fast)
        duplicate_count = vector_store_service.get_duplicate_count()
        
        return {
            "total_documents": document_count,
            "duplicate_pairs": duplicate_count,
            "documents_with_duplicates": duplicate_count * 2 if duplicate_count > 0 else 0,
            "potential_merges": duplicate_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get duplicate summary: {str(e)}")


# Clear all data
@app.delete("/clear")
async def clear_all_data():
    """Clear all documents from the vector store."""
    try:
        global vector_store_service
        
        if not vector_store_service:
            raise HTTPException(status_code=400, detail="Vector store not initialized")
        
        success, message = vector_store_service.clear_all_documents()
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


# Background processing function
async def process_documents_background(processing_id: str, request: ProcessingRequest):
    """Background task for processing documents."""
    global confluence_service, vector_store_service
    
    try:
        # Update status
        processing_status[processing_id].update({
            "status": "connecting",
            "message": "Connecting to Confluence..."
        })
        
        # Initialize Confluence service
        confluence_service = ConfluenceService(
            base_url=request.credentials.base_url,
            username=request.credentials.username,
            api_token=request.credentials.api_token
        )
        
        # Test connection
        conn_success, conn_message = confluence_service.test_connection()
        if not conn_success:
            processing_status[processing_id].update({
                "status": "failed",
                "message": f"Confluence connection failed: {conn_message}"
            })
            return
        
        # Initialize vector store if not already done
        if not vector_store_service:
            vector_store_service = VectorStoreConfig.create_service_from_env()
        
        # Update status
        processing_status[processing_id].update({
            "status": "loading",
            "message": f"Loading documents from {len(request.space_keys)} spaces..."
        })
        
        # Load documents from Confluence
        load_success, documents, load_message = confluence_service.load_all_pages_from_spaces(
            space_keys=request.space_keys,
            limit_per_space=request.limit_per_space
        )
        
        if not load_success:
            processing_status[processing_id].update({
                "status": "failed",
                "message": f"Document loading failed: {load_message}"
            })
            return
        
        processing_status[processing_id].update({
            "documents_loaded": len(documents),
            "message": f"Loaded {len(documents)} documents, adding to vector store..."
        })
        
        # Add documents to vector store
        add_success, add_message = vector_store_service.add_documents(documents)
        
        if not add_success:
            processing_status[processing_id].update({
                "status": "failed",
                "message": f"Vector store addition failed: {add_message}"
            })
            return
        
        # Update status
        processing_status[processing_id].update({
            "status": "scanning_duplicates",
            "message": "Scanning for duplicate documents..."
        })
        
        # Scan for duplicates
        scan_success, scan_results = vector_store_service.scan_for_duplicates(
            similarity_threshold=request.similarity_threshold,
            update_existing=True
        )
        
        if scan_success:
            processing_status[processing_id].update({
                "status": "completed",
                "message": "Processing completed successfully",
                "duplicates_found": scan_results.get('pairs_found', 0),
                "documents_updated": scan_results.get('documents_updated', 0),
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
        else:
            processing_status[processing_id].update({
                "status": "completed_with_warnings",
                "message": f"Processing completed but duplicate scan had issues: {scan_results.get('message', 'Unknown error')}",
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
        
    except Exception as e:
        processing_status[processing_id].update({
            "status": "failed",
            "message": f"Processing failed: {str(e)}",
            "failed_at": datetime.now(timezone.utc).isoformat()
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
