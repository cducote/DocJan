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
    
    print("🚀 [STARTUP] Application starting up...")
    print(f"🚀 [STARTUP] Environment check - OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"🚀 [STARTUP] Environment check - ChromaDB persist dir: {os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')}")
    print(f"🚀 [STARTUP] Current working directory: {os.getcwd()}")
    
    try:
        print("🗄️ [STARTUP] Initializing vector store service from environment...")
        # Initialize vector store service from environment
        vector_store_service = VectorStoreConfig.create_service_from_env()
        print("✅ [STARTUP] Vector store service initialized successfully")
        
        # Test the vector store
        try:
            print("🧪 [STARTUP] Testing vector store connection...")
            vs_success, vs_message = vector_store_service.test_connection()
            if vs_success:
                print(f"✅ [STARTUP] Vector store test successful: {vs_message}")
                doc_count = vector_store_service.get_document_count()
                print(f"📊 [STARTUP] Vector store contains {doc_count} documents")
            else:
                print(f"❌ [STARTUP] Vector store test failed: {vs_message}")
        except Exception as vs_test_error:
            print(f"💥 [STARTUP] Vector store test error: {vs_test_error}")
            print(f"💥 [STARTUP] Error type: {type(vs_test_error).__name__}")
            import traceback
            print(f"💥 [STARTUP] Traceback: {traceback.format_exc()}")
            
    except Exception as e:
        print(f"❌ [STARTUP] Vector store service initialization failed: {e}")
        print(f"❌ [STARTUP] Error type: {type(e).__name__}")
        import traceback
        print(f"❌ [STARTUP] Traceback: {traceback.format_exc()}")
        print(f"❌ [STARTUP] Will try to initialize on first request")
        # Continue without vector store - will be initialized on first request


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "vector_store": vector_store_service is not None,
            "confluence": confluence_service is not None
        },
        "environment": {
            "openai_api_key_set": bool(os.getenv('OPENAI_API_KEY')),
            "chroma_persist_dir": os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store'),
            "working_directory": os.getcwd()
        }
    }
    
    # Test vector store if available
    if vector_store_service:
        try:
            vs_success, vs_message = vector_store_service.test_connection()
            doc_count = vector_store_service.get_document_count()
            health_info["vector_store_details"] = {
                "connected": vs_success,
                "message": vs_message,
                "document_count": doc_count
            }
        except Exception as e:
            health_info["vector_store_details"] = {
                "connected": False,
                "error": str(e)
            }
    
    print(f"🩺 [HEALTH] Health check result: {health_info}")
    return health_info


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
        print("🔍 [CONNECTION-STATUS] Checking system status...")
        
        # Check vector store
        vector_store_connected = False
        document_count = 0
        
        if vector_store_service:
            print("🔍 [CONNECTION-STATUS] Vector store service exists, testing connection...")
            vs_success, vs_message = vector_store_service.test_connection()
            print(f"🔍 [CONNECTION-STATUS] Vector store test result: {vs_success}, message: {vs_message}")
            vector_store_connected = vs_success
            if vs_success:
                try:
                    document_count = vector_store_service.get_document_count()
                    print(f"🔍 [CONNECTION-STATUS] Document count: {document_count}")
                except Exception as count_error:
                    print(f"❌ [CONNECTION-STATUS] Failed to get document count: {count_error}")
                    document_count = 0
        else:
            print("❌ [CONNECTION-STATUS] Vector store service is None")
        
        # Determine overall status
        if vector_store_connected:
            if document_count > 0:
                status = "ready"
            else:
                status = "connected_no_data"
        else:
            status = "not_configured"
        
        result = ConnectionStatus(
            confluence_connected=confluence_service is not None,
            vector_store_connected=vector_store_connected,
            document_count=document_count,
            status=status
        )
        
        print(f"🔍 [CONNECTION-STATUS] Final result: {result}")
        return result
        
    except Exception as e:
        print(f"💥 [CONNECTION-STATUS] Error getting status: {e}")
        print(f"💥 [CONNECTION-STATUS] Error type: {type(e).__name__}")
        import traceback
        print(f"💥 [CONNECTION-STATUS] Traceback: {traceback.format_exc()}")
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
    
    print(f"🚀 [PROCESSING {processing_id}] Starting background processing")
    print(f"📋 [PROCESSING {processing_id}] Request details: {len(request.space_keys)} spaces, threshold: {request.similarity_threshold}")
    
    try:
        # Update status
        processing_status[processing_id].update({
            "status": "connecting",
            "message": "Connecting to Confluence..."
        })
        
        print(f"🔗 [PROCESSING {processing_id}] Initializing Confluence service...")
        print(f"🔗 [PROCESSING {processing_id}] Base URL: {request.credentials.base_url}")
        print(f"🔗 [PROCESSING {processing_id}] Username: {request.credentials.username}")
        
        # Initialize Confluence service
        confluence_service = ConfluenceService(
            base_url=request.credentials.base_url,
            username=request.credentials.username,
            api_token=request.credentials.api_token
        )
        
        # Test connection
        print(f"🧪 [PROCESSING {processing_id}] Testing Confluence connection...")
        conn_success, conn_message = confluence_service.test_connection()
        if not conn_success:
            print(f"❌ [PROCESSING {processing_id}] Confluence connection failed: {conn_message}")
            processing_status[processing_id].update({
                "status": "failed",
                "message": f"Confluence connection failed: {conn_message}"
            })
            return
        
        print(f"✅ [PROCESSING {processing_id}] Confluence connection successful")
        
        # Initialize vector store if not already done
        print(f"🗄️ [PROCESSING {processing_id}] Checking vector store service...")
        if not vector_store_service:
            try:
                print(f"🗄️ [PROCESSING {processing_id}] Creating new vector store service...")
                vector_store_service = VectorStoreConfig.create_service_from_env()
                print(f"✅ [PROCESSING {processing_id}] Vector store service initialized")
            except Exception as vs_init_error:
                print(f"💥 [PROCESSING {processing_id}] Vector store initialization failed: {vs_init_error}")
                print(f"💥 [PROCESSING {processing_id}] Error type: {type(vs_init_error).__name__}")
                import traceback
                print(f"💥 [PROCESSING {processing_id}] Traceback: {traceback.format_exc()}")
                processing_status[processing_id].update({
                    "status": "failed",
                    "message": f"Vector store initialization failed: {vs_init_error}"
                })
                return
        else:
            print(f"✅ [PROCESSING {processing_id}] Using existing vector store service")
        
        # Check vector store status
        print(f"🔍 [PROCESSING {processing_id}] Checking vector store status...")
        try:
            vs_success, vs_message = vector_store_service.test_connection()
            if vs_success:
                print(f"✅ [PROCESSING {processing_id}] Vector store connection test passed: {vs_message}")
                doc_count = vector_store_service.get_document_count()
                print(f"📊 [PROCESSING {processing_id}] Current vector store has {doc_count} documents")
            else:
                print(f"❌ [PROCESSING {processing_id}] Vector store connection test failed: {vs_message}")
                processing_status[processing_id].update({
                    "status": "failed",
                    "message": f"Vector store connection test failed: {vs_message}"
                })
                return
        except Exception as vs_error:
            print(f"💥 [PROCESSING {processing_id}] Vector store test error: {vs_error}")
            print(f"💥 [PROCESSING {processing_id}] Error type: {type(vs_error).__name__}")
            import traceback
            print(f"💥 [PROCESSING {processing_id}] Traceback: {traceback.format_exc()}")
            processing_status[processing_id].update({
                "status": "failed",
                "message": f"Vector store test error: {vs_error}"
            })
            return
        
        # Update status
        processing_status[processing_id].update({
            "status": "loading",
            "message": f"Loading documents from {len(request.space_keys)} spaces..."
        })
        
        print(f"📚 [PROCESSING {processing_id}] Loading documents from spaces: {request.space_keys}")
        
        # Load documents from Confluence
        load_success, documents, load_message = confluence_service.load_all_pages_from_spaces(
            space_keys=request.space_keys,
            limit_per_space=request.limit_per_space
        )
        
        if not load_success:
            print(f"❌ [PROCESSING {processing_id}] Document loading failed: {load_message}")
            processing_status[processing_id].update({
                "status": "failed",
                "message": f"Document loading failed: {load_message}"
            })
            return
        
        print(f"✅ [PROCESSING {processing_id}] Loaded {len(documents)} documents from Confluence")
        
        processing_status[processing_id].update({
            "documents_loaded": len(documents),
            "message": f"Loaded {len(documents)} documents, adding to vector store..."
        })
        
        # Add documents to vector store
        print(f"💾 [PROCESSING {processing_id}] Adding {len(documents)} documents to vector store...")
        try:
            add_success, add_message = vector_store_service.add_documents(documents)
            
            if not add_success:
                print(f"❌ [PROCESSING {processing_id}] Vector store addition failed: {add_message}")
                processing_status[processing_id].update({
                    "status": "failed",
                    "message": f"Vector store addition failed: {add_message}"
                })
                return
            
            print(f"✅ [PROCESSING {processing_id}] Documents successfully added to vector store: {add_message}")
        except Exception as add_error:
            print(f"💥 [PROCESSING {processing_id}] Vector store addition error: {add_error}")
            print(f"💥 [PROCESSING {processing_id}] Error type: {type(add_error).__name__}")
            import traceback
            print(f"💥 [PROCESSING {processing_id}] Traceback: {traceback.format_exc()}")
            processing_status[processing_id].update({
                "status": "failed",
                "message": f"Vector store addition error: {add_error}"
            })
            return
        
        # Check vector store status after adding
        try:
            new_doc_count = vector_store_service.get_document_count()
            print(f"📊 [PROCESSING {processing_id}] Vector store now has {new_doc_count} documents")
        except Exception as vs_error:
            print(f"⚠️ [PROCESSING {processing_id}] Could not get updated document count: {vs_error}")
        
        # Update status
        processing_status[processing_id].update({
            "status": "scanning_duplicates",
            "message": "Scanning for duplicate documents..."
        })
        
        # Scan for duplicates
        print(f"🔍 [PROCESSING {processing_id}] Scanning for duplicates with threshold {request.similarity_threshold}...")
        scan_success, scan_results = vector_store_service.scan_for_duplicates(
            similarity_threshold=request.similarity_threshold,
            update_existing=True
        )
        
        if scan_success:
            print(f"✅ [PROCESSING {processing_id}] Duplicate scan completed successfully")
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
        print(f"💥 [PROCESSING {processing_id}] CRITICAL ERROR: {str(e)}")
        print(f"💥 [PROCESSING {processing_id}] Error type: {type(e).__name__}")
        import traceback
        print(f"💥 [PROCESSING {processing_id}] Traceback: {traceback.format_exc()}")
        
        processing_status[processing_id].update({
            "status": "failed",
            "message": f"Processing failed: {str(e)}",
            "failed_at": datetime.now(timezone.utc).isoformat()
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
