"""
FastAPI Application for Confluence Document Processing Service.
Clean, containerized backend for connecting to Confluence, processing documents,
and generating embeddings.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import asyncio
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our service modules
try:
    from .confluence_service import ConfluenceService, ConfluenceConfig
    from .vector_store_service import VectorStoreService, VectorStoreConfig
    from .duplicate_storage import DuplicateStorageService
except ImportError:
    # When running directly, use absolute imports
    from confluence_service import ConfluenceService, ConfluenceConfig
    from vector_store_service import VectorStoreService, VectorStoreConfig
    from duplicate_storage import DuplicateStorageService

# Import logging
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize logger
logger = logging.getLogger("main")

# Define logging helper functions
def log_startup(message):
    logger.info(f"🚀 {message}")

def log_shutdown(message):
    logger.info(f"🛑 {message}")

def log_api_request(endpoint, method="", **kwargs):
    extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()]) if kwargs else ""
    logger.info(f"📨 API {method} {endpoint}{' | ' + extra_info if extra_info else ''}")

def log_api_response(logger_param, endpoint, status_code, duration_ms=None, **kwargs):
    duration_info = f" | {duration_ms:.1f}ms" if duration_ms else ""
    extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()]) if kwargs else ""
    status_emoji = "✅" if status_code < 400 else "❌"
    logger.info(f"{status_emoji} API {endpoint} → {status_code}{duration_info}{' | ' + extra_info if extra_info else ''}")

def log_error_with_context(logger_param, error, context="", **kwargs):
    import traceback
    context_info = f" | Context: {context}" if context else ""
    extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()]) if kwargs else ""
    logger.error(f"💥 ERROR: {str(error)}{context_info}{' | ' + extra_info if extra_info else ''}")
    logger.debug(f"🔍 Full traceback:\n{traceback.format_exc()}")

# Initialize FastAPI app
app = FastAPI(
    title="Confluence Document Processing API",
    description="Containerized service for Confluence document ingestion, vectorization, and duplicate detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://concatly.vercel.app",  # Vercel production
        "https://*.vercel.app",  # Vercel preview deployments
        "*"  # Fallback for other origins
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global service instances (will be initialized on startup)
confluence_service: Optional[ConfluenceService] = None
vector_store_service: Optional[VectorStoreService] = None
duplicate_storage_service: Optional[DuplicateStorageService] = None

# Organization-specific vector store services cache
organization_vector_stores: Dict[str, VectorStoreService] = {}

# In-memory status tracking
processing_status = {}


def get_vector_store_for_organization(organization_id: Optional[str] = None) -> VectorStoreService:
    """
    Get or create a vector store service for the specified organization.
    
    Args:
        organization_id: Organization ID for data isolation. If None, uses global service.
        
    Returns:
        VectorStoreService instance for the organization
    """
    global vector_store_service, organization_vector_stores
    
    # If no organization_id provided, use global service (for backward compatibility)
    if not organization_id:
        if vector_store_service is None:
            print("🔄 [VECTOR_STORE] Creating global vector store service...")
            vector_store_service = VectorStoreConfig.create_service_from_env()
        return vector_store_service
    
    # Check if we already have a service for this organization
    if organization_id in organization_vector_stores:
        return organization_vector_stores[organization_id]
    
    # Create new organization-specific service
    print(f"🔄 [VECTOR_STORE] Creating vector store service for organization: {organization_id}")
    org_service = VectorStoreConfig.create_service_from_env(organization_id)
    organization_vector_stores[organization_id] = org_service
    
    return org_service


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
    organization_id: Optional[str] = Field(None, description="Organization ID for data isolation")


class ConnectionStatusRequest(BaseModel):
    """Request for connection status with organization context."""
    organization_id: Optional[str] = Field(None, description="Organization ID for data isolation")


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


class MergeRequest(BaseModel):
    """Request to merge two documents."""
    pair_id: int = Field(..., description="ID of the duplicate pair to merge")
    organization_id: Optional[str] = Field(None, description="Organization ID for data isolation")


class ApplyMergeRequest(BaseModel):
    """Request to apply a merge to Confluence."""
    pair_id: int = Field(..., description="ID of the duplicate pair")
    organization_id: Optional[str] = Field(None, description="Organization ID for data isolation")
    merged_content: str = Field(..., description="The merged content to apply")
    keep_main: bool = Field(..., description="Whether to keep the main document's title/page")
    user_credentials: Optional[dict] = Field(None, description="User's Confluence credentials")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global vector_store_service, duplicate_storage_service
    
    # Log startup
    log_startup("main")
    
    try:
        logger.info("🔑 Environment check - OpenAI API Key: ✅ Set" if os.getenv('OPENAI_API_KEY') else "🔑 Environment check - OpenAI API Key: ❌ Missing")
        logger.info(f"🗄️ Environment check - ChromaDB persist dir: {os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')}")
        logger.info(f"📂 Current working directory: {os.getcwd()}")
        
        logger.info("🗄️ Initializing vector store service from environment...")
        # Initialize vector store service from environment
        vector_store_service = VectorStoreConfig.create_service_from_env()
        logger.info("✅ Vector store service initialized successfully")
        
        logger.info("💾 Initializing duplicate storage service...")
        # Initialize duplicate storage service
        duplicate_storage_service = DuplicateStorageService()
        storage_info = duplicate_storage_service.get_storage_info()
        logger.info(f"✅ Duplicate storage initialized: {storage_info['storage_type']}")
        
        # Test the vector store
        try:
            logger.info("🧪 Testing vector store connection...")
            vs_success, vs_message = vector_store_service.test_connection_lightweight()
            if vs_success:
                logger.info(f"✅ Vector store test successful: {vs_message}")
                doc_count = vector_store_service.get_document_count()
                logger.info(f"📊 Vector store contains {doc_count} documents")
            else:
                logger.error(f"❌ Vector store test failed: {vs_message}")
        except Exception as vs_test_error:
            log_error_with_context(logger, vs_test_error, "vector store test")
            
    except Exception as e:
        log_error_with_context(logger, e, "vector store service initialization")
        logger.warning("Will try to initialize on first request")


# CORS preflight handler
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    from fastapi import Response
    return Response(status_code=200)

# Simple ping endpoint for ALB health checks
@app.get("/ping")
async def ping():
    """Simple ping endpoint that doesn't require any services."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    start_time = time.time()
    
    try:
        # Get vector store status using lightweight test (no OpenAI API calls)
        vs_service = get_vector_store_for_organization()
        vs_connected, vs_message = vs_service.test_connection_lightweight()
        
        doc_count = vs_service.get_document_count() if vs_connected else 0
        
        status = {
            "status": "healthy" if vs_connected else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "vector_store": {
                    "connected": vs_connected,
                    "message": vs_message,
                    "document_count": doc_count
                }
            }
        }
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_response(logger, "/health", 200, duration_ms, doc_count=doc_count)
        
        return status
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error_with_context(logger, e, "/health endpoint")
        log_api_response(logger, "/health", 500, duration_ms)
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancer health checks - no logging."""
    return {"status": "ok"}


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


# Get connection status (both GET for backward compatibility and POST for organization-specific)
@app.get("/connection-status")
async def get_connection_status(organization_id: Optional[str] = None) -> ConnectionStatus:
    """Get overall connection and system status with optional organization context."""
    return await get_connection_status_for_org(ConnectionStatusRequest(organization_id=organization_id))


@app.post("/connection-status")
async def get_connection_status_for_org(request: ConnectionStatusRequest) -> ConnectionStatus:
    """Get connection and system status for specific organization."""
    try:
        organization_id = request.organization_id
        print(f"🔍 [CONNECTION-STATUS] Checking system status for organization: {organization_id or 'default'}")
        
        # Get organization-specific vector store
        org_vector_store = get_vector_store_for_organization(organization_id)
        
        # Check vector store
        vector_store_connected = False
        document_count = 0
        
        if org_vector_store:
            print(f"🔍 [CONNECTION-STATUS] Vector store service exists for org {organization_id or 'default'}, testing connection...")
            vs_success, vs_message = org_vector_store.test_connection()
            print(f"🔍 [CONNECTION-STATUS] Vector store test result: {vs_success}, message: {vs_message}")
            vector_store_connected = vs_success
            if vs_success:
                try:
                    # Use stored metadata instead of expensive ChromaDB query
                    if duplicate_storage_service and organization_id:
                        metadata = duplicate_storage_service.get_organization_metadata(organization_id)
                        if metadata and metadata.get('total_documents'):
                            document_count = metadata['total_documents']
                            print(f"🔍 [CONNECTION-STATUS] Using stored document count for org {organization_id}: {document_count}")
                        else:
                            # Fallback to ChromaDB only if no stored metadata
                            document_count = org_vector_store.get_document_count()
                            print(f"🔍 [CONNECTION-STATUS] No stored metadata, using ChromaDB count for org {organization_id}: {document_count}")
                    else:
                        # Fallback to ChromaDB for non-organization requests
                        document_count = org_vector_store.get_document_count()
                        print(f"🔍 [CONNECTION-STATUS] Using ChromaDB count for org {organization_id or 'default'}: {document_count}")
                except Exception as count_error:
                    print(f"❌ [CONNECTION-STATUS] Failed to get document count: {count_error}")
                    document_count = 0
        else:
            print(f"❌ [CONNECTION-STATUS] Vector store service is None for org {organization_id or 'default'}")
        
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
        
        print(f"🔍 [CONNECTION-STATUS] Final result for org {organization_id or 'default'}: {result}")
        return result
        
    except Exception as e:
        print(f"💥 [CONNECTION-STATUS] Error getting status: {e}")
        print(f"💥 [CONNECTION-STATUS] Error type: {type(e).__name__}")
        import traceback
        print(f"💥 [CONNECTION-STATUS] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


# Get duplicates
@app.post("/scan-duplicates")
async def scan_duplicates_manual(request: ConnectionStatusRequest):
    """Manually trigger duplicate scanning for an organization to populate cache."""
    try:
        organization_id = request.organization_id
        print(f"🔍 [MANUAL_SCAN] Starting manual duplicate scan for organization: {organization_id}")
        
        # Get organization-specific vector store
        org_vector_store = get_vector_store_for_organization(organization_id)
        
        if not org_vector_store:
            raise HTTPException(status_code=400, detail="Vector store not initialized")
        
        # Run duplicate scanning
        success, result = org_vector_store.scan_for_duplicates(similarity_threshold=0.65)
        
        if success:
            return {
                "success": True,
                "message": f"Duplicate scan completed successfully. Found {result['pairs_found']} pairs.",
                "pairs_found": result['pairs_found'],
                "documents_updated": result['documents_updated']
            }
        else:
            return {
                "success": False,
                "message": result['message'],
                "pairs_found": result.get('pairs_found', 0)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [MANUAL_SCAN] Error during manual scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scan duplicates: {str(e)}")


async def refresh_duplicates_for_organization(organization_id: str, force_rescan: bool = False) -> bool:
    """Refresh duplicate detection for an organization and store results."""
    try:
        logger.info(f"🔄 Starting duplicate refresh for organization {organization_id}")
        
        # First check if we already have stored data (unless force rescan)
        if duplicate_storage_service and not force_rescan:
            stored_data = duplicate_storage_service.get_duplicate_pairs(organization_id)
            if stored_data:
                logger.info(f"✅ Using existing stored data for {organization_id} (last updated: {stored_data.get('last_updated')})")
                return True
        
        # Only perform expensive scan if no stored data exists or force_rescan is True
        if force_rescan:
            logger.info(f"🔍 Force rescan requested for {organization_id}")
        else:
            logger.info(f"🔍 No stored data found, performing duplicate scan for {organization_id}")
        
        # Get organization-specific vector store
        org_vector_store = get_vector_store_for_organization(organization_id)
        
        if not org_vector_store:
            logger.error(f"❌ Vector store not initialized for {organization_id}")
            return False
        
        # Perform expensive duplicate detection
        duplicates = org_vector_store.get_duplicates()
        
        # Store results in persistent storage
        success = duplicate_storage_service.store_duplicate_pairs(organization_id, duplicates)
        
        if success:
            logger.info(f"✅ Stored {len(duplicates)} duplicate pairs for {organization_id}")
        else:
            logger.error(f"❌ Failed to store duplicate pairs for {organization_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to refresh duplicates for {organization_id}: {str(e)}")
        return False


@app.get("/duplicates")
async def get_duplicates(organization_id: Optional[str] = None) -> List[DuplicatePair]:
    """Get all detected duplicate document pairs for organization."""
    try:
        if not duplicate_storage_service:
            raise HTTPException(status_code=500, detail="Storage service not initialized")
        
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
        
        # Get unresolved duplicate pairs from storage
        unresolved_pairs = duplicate_storage_service.get_unresolved_pairs(organization_id)
        
        # If no stored pairs, trigger a fresh scan
        if not unresolved_pairs:
            logger.info(f"🔍 No stored duplicates found for {organization_id}, triggering fresh scan...")
            await refresh_duplicates_for_organization(organization_id)
            unresolved_pairs = duplicate_storage_service.get_unresolved_pairs(organization_id)
        
        return [DuplicatePair(**pair) for pair in unresolved_pairs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get duplicates: {str(e)}")


# Get duplicate summary (fast, just counts)
@app.get("/duplicates/summary")
async def get_duplicate_summary(organization_id: Optional[str] = None):
    """Get duplicate summary without expensive calculations for organization."""
    try:
        if not duplicate_storage_service:
            raise HTTPException(status_code=500, detail="Storage service not initialized")
        
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
        
        # First try to get metadata (fast)
        metadata = duplicate_storage_service.get_organization_metadata(organization_id)
        
        if metadata:
            logger.info(f"📊 Using stored metadata for {organization_id}")
            return {
                "total_documents": metadata.get("total_documents", 0),
                "duplicate_pairs": metadata.get("pending_duplicate_pairs", 0),
                "documents_with_duplicates": metadata.get("documents_with_duplicates", 0),
                "potential_merges": metadata.get("pending_duplicate_pairs", 0),
                "last_updated": metadata.get("last_updated"),
                "last_ingestion": metadata.get("last_ingestion"),
                "spaces_indexed": metadata.get("spaces_indexed", [])
            }
        
        # Fallback: try duplicate pairs data
        stored_pairs = duplicate_storage_service.get_duplicate_pairs(organization_id)
        
        if stored_pairs:
            logger.info(f"📊 Using stored duplicate pairs for {organization_id}")
            unresolved_pairs = duplicate_storage_service.get_unresolved_pairs(organization_id)
            
            return {
                "total_documents": stored_pairs.get("total_documents", 0),
                "duplicate_pairs": len(unresolved_pairs),
                "documents_with_duplicates": len(unresolved_pairs) * 2 if unresolved_pairs else 0,
                "potential_merges": len(unresolved_pairs),
                "last_updated": stored_pairs.get("last_updated")
            }
        
        # Last resort: query vector store (slow)
        logger.warning(f"⚠️ No stored data found, querying vector store for {organization_id}")
        org_vector_store = get_vector_store_for_organization(organization_id)
        
        if not org_vector_store:
            return {
                "total_documents": 0,
                "duplicate_pairs": 0,
                "documents_with_duplicates": 0,
                "potential_merges": 0,
                "last_updated": None
            }
        
        document_count = org_vector_store.get_document_count()
        
        return {
            "total_documents": document_count,
            "duplicate_pairs": 0,
            "documents_with_duplicates": 0,
            "potential_merges": 0,
            "last_updated": None
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get duplicate summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get duplicate summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get duplicate summary: {str(e)}")


# Clear all data for organization
@app.post("/clear-organization-data")
async def clear_organization_data(request: ConnectionStatusRequest):
    """Clear all documents, cache, and metadata for a specific organization."""
    try:
        organization_id = request.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
            
        print(f"🗑️ [CLEAR] Clearing all data for organization: {organization_id}")
        
        # Get the organization-specific vector store
        vs_service = get_vector_store_for_organization(organization_id)
        
        # Clear vector store documents
        success, message = vs_service.clear_all_documents()
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        # Reset only connection status fields in metadata (preserve duplicate history)
        if duplicate_storage_service:
            # Only reset document count and connection-related fields, preserve duplicate history
            reset_updates = {
                "total_documents": 0,
                "total_pages": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "status": "cleared"
            }
            metadata_updated = duplicate_storage_service.update_organization_metadata(organization_id, reset_updates)
            if metadata_updated:
                print(f"✅ [CLEAR] Reset connection status in metadata for: {organization_id}")
            else:
                print(f"⚠️ [CLEAR] Failed to reset connection status in metadata for: {organization_id}")
        
        print(f"✅ [CLEAR] Successfully cleared documents and reset connection status for organization: {organization_id}")
        return {"success": True, "message": f"{message}. Connection status reset to show system needs setup.", "organization_id": organization_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [CLEAR] Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear organization data: {str(e)}")


# Clear all data (legacy endpoint - kept for backward compatibility)
@app.delete("/clear")
async def clear_all_data(organization_id: Optional[str] = None):
    """Clear all documents from the vector store."""
    try:
        # Get the organization-specific vector store
        vs_service = get_vector_store_for_organization(organization_id)
        
        success, message = vs_service.clear_all_documents()
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


# Merge endpoints
@app.get("/merge/documents/{pair_id}")
async def get_merge_documents(pair_id: int, organization_id: Optional[str] = None):
    """Get full document content for a duplicate pair to enable merging."""
    start_time = time.time()
    log_api_request(f"/merge/documents/{pair_id}", "GET", organization_id=organization_id)
    
    try:
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
        
        # Use stored duplicate pairs instead of expensive ChromaDB query
        stored_pairs = []
        if duplicate_storage_service:
            unresolved_pairs = duplicate_storage_service.get_unresolved_pairs(organization_id)
            if unresolved_pairs:
                stored_pairs = unresolved_pairs
                logger.info(f"📊 Using stored duplicate pairs: {len(stored_pairs)} unresolved pairs")
        
        # Fallback to vector store only if no stored pairs
        if not stored_pairs:
            logger.warning(f"⚠️ No stored pairs found, falling back to vector store query")
            vs_service = get_vector_store_for_organization(organization_id)
            stored_pairs = vs_service.get_duplicate_pairs()
        
        logger.debug(f"Found {len(stored_pairs)} duplicate pairs")
        
        # Find the specific pair
        target_pair = None
        for pair in stored_pairs:
            if pair['id'] == pair_id:
                target_pair = pair
                break
        
        if not target_pair:
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(logger, f"/merge/documents/{pair_id}", 404, duration_ms)
            raise HTTPException(status_code=404, detail=f"Duplicate pair {pair_id} not found")
        
        logger.info(f"Found target pair: {target_pair['page1']['title']} <-> {target_pair['page2']['title']}")
        
        # Get vector store only for document content retrieval
        vs_service = get_vector_store_for_organization(organization_id)
        
        # Get full document content from vector store
        main_doc_data = vs_service.get_document_by_metadata(target_pair['page1'])
        similar_doc_data = vs_service.get_document_by_metadata(target_pair['page2'])
        
        if not main_doc_data or not similar_doc_data:
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(logger, f"/merge/documents/{pair_id}", 404, duration_ms)
            raise HTTPException(status_code=404, detail="Could not retrieve full document content")
        
        result = {
            "main_doc": {
                "title": target_pair['page1']['title'],
                "url": target_pair['page1']['url'],
                "space": target_pair['page1'].get('space', ''),
                "content": main_doc_data['content'],
                "metadata": main_doc_data['metadata']
            },
            "similar_doc": {
                "title": target_pair['page2']['title'],
                "url": target_pair['page2']['url'],
                "space": target_pair['page2'].get('space', ''),
                "content": similar_doc_data['content'],
                "metadata": similar_doc_data['metadata']
            },
            "similarity": target_pair['similarity']
        }
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_response(logger, f"/merge/documents/{pair_id}", 200, duration_ms, 
                        similarity=target_pair['similarity'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error_with_context(logger, e, f"get_merge_documents pair_id={pair_id}")
        log_api_response(logger, f"/merge/documents/{pair_id}", 500, duration_ms)
        raise HTTPException(status_code=500, detail=f"Failed to get merge documents: {str(e)}")


@app.post("/merge/perform")
async def perform_merge(request: MergeRequest):
    """Perform AI-powered merge of two documents."""
    try:
        # Use stored duplicate pairs instead of expensive ChromaDB query
        duplicate_pairs = []
        if duplicate_storage_service:
            stored_data = duplicate_storage_service.get_duplicate_pairs(request.organization_id)
            if stored_data and stored_data.get('duplicate_pairs'):
                duplicate_pairs = stored_data['duplicate_pairs']
                print(f"📊 [PERFORM_MERGE] Using stored duplicate pairs: {len(duplicate_pairs)} pairs")
        
        # Fallback to vector store only if no stored pairs
        if not duplicate_pairs:
            print(f"⚠️ [PERFORM_MERGE] No stored pairs found, falling back to vector store query")
            vs_service = get_vector_store_for_organization(request.organization_id)
            duplicate_pairs = vs_service.get_duplicate_pairs()
        
        # Find the specific pair
        target_pair = None
        for pair in duplicate_pairs:
            if pair['id'] == request.pair_id:
                target_pair = pair
                break
        
        if not target_pair:
            raise HTTPException(status_code=404, detail=f"Duplicate pair {request.pair_id} not found")
        
        # Get vector store only for document content retrieval
        vs_service = get_vector_store_for_organization(request.organization_id)
        
        # Get full document content
        main_doc_data = vs_service.get_document_by_metadata(target_pair['page1'])
        similar_doc_data = vs_service.get_document_by_metadata(target_pair['page2'])
        
        if not main_doc_data or not similar_doc_data:
            raise HTTPException(status_code=404, detail="Could not retrieve full document content")
        
        # Create document objects for the AI merge function
        from ai.merging import merge_documents_with_ai
        
        # Create mock document objects that match the expected structure
        class MockDocument:
            def __init__(self, content, metadata):
                self.page_content = content
                self.metadata = metadata
        
        main_doc = MockDocument(main_doc_data['content'], target_pair['page1'])
        similar_doc = MockDocument(similar_doc_data['content'], target_pair['page2'])
        
        # Perform the AI merge
        merged_content = merge_documents_with_ai(main_doc, similar_doc)
        
        return {"merged_content": merged_content}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform merge: {str(e)}")


@app.get("/merge/history")
async def get_merge_history(organization_id: Optional[str] = None, limit: int = 50):
    """Get merge operation history for an organization."""
    try:
        if not organization_id:
            raise HTTPException(status_code=400, detail="organization_id is required")
        
        from services.merge_operations_storage import merge_operations_storage
        
        # Get merge operations for the organization
        merge_data = merge_operations_storage.get_merge_operations(organization_id)
        operations = merge_data.get('operations', [])
        
        # Sort by timestamp (newest first)
        operations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit
        return operations[:limit]
        
    except Exception as e:
        print(f"Error getting merge history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get merge history: {str(e)}")


@app.post("/merge/undo")
async def undo_merge_operation_endpoint(request: dict):
    """Undo a completed merge operation with sequential validation."""
    try:
        merge_id = request.get('merge_id')
        organization_id = request.get('organization_id')
        user_credentials = request.get('user_credentials')
        
        if not merge_id:
            raise HTTPException(status_code=400, detail="merge_id is required")
        if not organization_id:
            raise HTTPException(status_code=400, detail="organization_id is required")
        
        print(f"🔍 [UNDO_MERGE] Received request for merge_id: {merge_id}")
        print(f"🔍 [UNDO_MERGE] Organization ID: {organization_id}")
        print(f"🔍 [UNDO_MERGE] User credentials provided: {bool(user_credentials)}")
        
        from services.merge_operations_storage import merge_operations_storage
        
        # Validate if this operation can be undone
        validation = merge_operations_storage.validate_undo_sequence(organization_id, merge_id)
        
        if not validation['can_undo']:
            print(f"❌ [UNDO_MERGE] Cannot undo: {validation['reason']}")
            
            if validation.get('required_undos'):
                next_undo = validation.get('next_required_undo')
                return {
                    "success": False,
                    "reason": validation['reason'],
                    "requires_sequential_undo": True,
                    "next_required_undo": next_undo,
                    "blocking_operations": validation['required_undos']
                }
            else:
                raise HTTPException(status_code=400, detail=validation['reason'])
        
        # Import the undo functionality
        from confluence.api import undo_merge_operation
        
        success, message = undo_merge_operation(merge_id, user_credentials)
        
        if success:
            print(f"✅ [UNDO_MERGE] Undo operation successful: {message}")
            return {"success": True, "message": message}
        else:
            print(f"❌ [UNDO_MERGE] Undo operation failed: {message}")
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        print(f"❌ [UNDO_MERGE] Error undoing merge: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to undo merge: {str(e)}")


@app.post("/merge/apply")
async def apply_merge(request: ApplyMergeRequest):
    """Apply the merged content to Confluence."""
    try:
        print(f"🔍 [APPLY_MERGE] Received request with user_credentials: {bool(request.user_credentials)}")
        if request.user_credentials:
            print(f"🔍 [APPLY_MERGE] User credentials keys: {list(request.user_credentials.keys())}")
            print(f"🔍 [APPLY_MERGE] Raw user credentials: {request.user_credentials}")
        else:
            print("⚠️ [APPLY_MERGE] No user credentials received in request!")
        
        print(f"🔍 [APPLY_MERGE] Getting vector store for org: {request.organization_id}")
        # Get the organization-specific vector store
        vs_service = get_vector_store_for_organization(request.organization_id)
        
        print(f"🔍 [APPLY_MERGE] Getting duplicate pairs...")
        # Use stored duplicate pairs instead of expensive ChromaDB query
        duplicate_pairs = []
        if duplicate_storage_service:
            stored_data = duplicate_storage_service.get_duplicate_pairs(request.organization_id)
            if stored_data and stored_data.get('duplicate_pairs'):
                duplicate_pairs = stored_data['duplicate_pairs']
                print(f"📊 [APPLY_MERGE] Using stored duplicate pairs: {len(duplicate_pairs)} pairs")
        
        # Fallback to vector store only if no stored pairs
        if not duplicate_pairs:
            print(f"⚠️ [APPLY_MERGE] No stored pairs found, falling back to vector store query")
            duplicate_pairs = vs_service.get_duplicate_pairs()
        
        print(f"🔍 [APPLY_MERGE] Found {len(duplicate_pairs)} duplicate pairs, looking for pair_id: {request.pair_id}")
        # Find the specific pair
        target_pair = None
        for pair in duplicate_pairs:
            if pair['id'] == request.pair_id:
                target_pair = pair
                break
        
        if not target_pair:
            print(f"❌ [APPLY_MERGE] Target pair {request.pair_id} not found!")
            raise HTTPException(status_code=404, detail=f"Duplicate pair {request.pair_id} not found")
        
        print(f"✅ [APPLY_MERGE] Found target pair: {target_pair}")
        
        print(f"🔍 [APPLY_MERGE] Getting document data...")
        # Get full document content to create proper document objects
        main_doc_data = vs_service.get_document_by_metadata(target_pair['page1'])
        similar_doc_data = vs_service.get_document_by_metadata(target_pair['page2'])
        
        if not main_doc_data or not similar_doc_data:
            print(f"❌ [APPLY_MERGE] Could not retrieve document data!")
            raise HTTPException(status_code=404, detail="Could not retrieve full document content")
        
        print(f"✅ [APPLY_MERGE] Retrieved document data successfully")
        
        # Create document objects for the Confluence API
        print(f"🔍 [APPLY_MERGE] Importing Confluence API...")
        from confluence.api import apply_merge_to_confluence
        
        print(f"🔍 [APPLY_MERGE] Creating document objects...")
        class MockDocument:
            def __init__(self, content, metadata):
                self.page_content = content
                self.metadata = metadata
        
        main_doc = MockDocument(main_doc_data['content'], target_pair['page1'])
        similar_doc = MockDocument(similar_doc_data['content'], target_pair['page2'])
        
        print(f"🔍 [APPLY_MERGE] Calling apply_merge_to_confluence with user_credentials...")
        # Apply the merge to Confluence
        success, message = apply_merge_to_confluence(
            main_doc, 
            similar_doc, 
            request.merged_content, 
            keep_main=request.keep_main,
            user_credentials=request.user_credentials,
            organization_id=request.organization_id
        )
        
        print(f"🔍 [APPLY_MERGE] apply_merge_to_confluence returned: success={success}, message={message}")
        
        if not success:
            print(f"❌ [APPLY_MERGE] Merge failed: {message}")
            raise HTTPException(status_code=500, detail=message)
        
        # Mark the duplicate pair as resolved in the vector store
        print(f"🔍 [APPLY_MERGE] Marking duplicate pair {request.pair_id} as resolved...")
        try:
            vs_service.mark_pair_as_resolved(request.pair_id)
            print(f"✅ [APPLY_MERGE] Successfully marked pair {request.pair_id} as resolved in vector store")
        except Exception as e:
            print(f"⚠️ [APPLY_MERGE] Failed to mark pair as resolved in vector store: {e}")
            # Don't fail the entire operation since the merge was successful
        
        # Also mark as resolved in our storage service
        try:
            if duplicate_storage_service:
                success = duplicate_storage_service.mark_pair_resolved(request.organization_id, str(request.pair_id))
                if success:
                    print(f"✅ [APPLY_MERGE] Successfully marked pair {request.pair_id} as resolved in storage")
                else:
                    print(f"⚠️ [APPLY_MERGE] Failed to mark pair as resolved in storage")
        except Exception as e:
            print(f"⚠️ [APPLY_MERGE] Error updating storage: {e}")

        print(f"✅ [APPLY_MERGE] Merge completed successfully!")
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 [APPLY_MERGE] Unexpected error: {e}")
        print(f"💥 [APPLY_MERGE] Error type: {type(e).__name__}")
        import traceback
        print(f"💥 [APPLY_MERGE] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to apply merge: {str(e)}")


@app.post("/refresh-duplicates")
async def refresh_duplicates(organization_id: Optional[str] = None, force: bool = False):
    """Force refresh of duplicate detection data after merge operations"""
    start_time = time.time()
    log_api_request("/refresh-duplicates", "POST", organization_id=organization_id)
    
    try:
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
        
        logger.info(f"🔄 [REFRESH_DUPLICATES] Starting refresh for organization {organization_id}")
        
        # Use our new refresh function
        success = await refresh_duplicates_for_organization(organization_id, force_rescan=force)
        
        if success:
            # Get the refreshed data to return stats
            stored_data = duplicate_storage_service.get_duplicate_pairs(organization_id)
            unresolved_pairs = duplicate_storage_service.get_unresolved_pairs(organization_id)
            
            duration_ms = (time.time() - start_time) * 1000
            
            log_api_response(logger, "/refresh-duplicates", 200, duration_ms, 
                           pairs_found=len(unresolved_pairs))
            
            return {
                "success": True,
                "message": "Duplicate detection refreshed successfully",
                "pairs_found": len(unresolved_pairs),
                "total_pairs": len(stored_data.get('duplicate_pairs', [])) if stored_data else 0,
                "last_updated": stored_data.get('last_updated') if stored_data else None,
                "duration_ms": duration_ms
            }
        else:
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(logger, "/refresh-duplicates", 500, duration_ms)
            raise HTTPException(status_code=500, detail="Failed to refresh duplicate detection")
            
    except HTTPException:
        duration_ms = (time.time() - start_time) * 1000
        log_api_response(logger, "/refresh-duplicates", 500, duration_ms)
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_response(logger, "/refresh-duplicates", 500, duration_ms)
        logger.error(f"❌ [REFRESH_DUPLICATES] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


# Cleanup endpoint for testing
@app.post("/cleanup-organization")
async def cleanup_organization(organization_id: Optional[str] = None):
    """Clean up all data for an organization (ChromaDB + storage) - for testing."""
    try:
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
        
        logger.info(f"🧹 Starting cleanup for organization {organization_id}")
        
        # Clear ChromaDB data
        try:
            org_vector_store = get_vector_store_for_organization(organization_id)
            if org_vector_store:
                # Reset the vector store (this will clear the collection)
                org_vector_store.reset()
                logger.info(f"✅ Cleared ChromaDB data for {organization_id}")
            
            # Remove from cache
            if organization_id in organization_vector_stores:
                del organization_vector_stores[organization_id]
                
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB cleanup failed: {e}")
        
        # Clear storage data
        if duplicate_storage_service:
            success = duplicate_storage_service.delete_organization_data(organization_id)
            if success:
                logger.info(f"✅ Cleared storage data for {organization_id}")
            else:
                logger.warning(f"⚠️ Storage cleanup failed for {organization_id}")
        
        return {
            "success": True,
            "message": f"Organization {organization_id} data cleared successfully",
            "organization_id": organization_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Apply merge operation
@app.post("/apply-merge")
# Background processing function
async def process_documents_background(processing_id: str, request: ProcessingRequest):
    """Background task for processing documents."""
    global confluence_service
    
    organization_id = request.organization_id
    print(f"🚀 [PROCESSING {processing_id}] Starting background processing for organization: {organization_id or 'default'}")
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
        
        # Get organization-specific vector store
        print(f"🗄️ [PROCESSING {processing_id}] Getting vector store service for organization: {organization_id or 'default'}")
        try:
            org_vector_store = get_vector_store_for_organization(organization_id)
            print(f"✅ [PROCESSING {processing_id}] Vector store service ready for organization: {organization_id or 'default'}")
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
        
        # Check vector store status
        print(f"🔍 [PROCESSING {processing_id}] Checking vector store status...")
        try:
            vs_success, vs_message = org_vector_store.test_connection()
            if vs_success:
                print(f"✅ [PROCESSING {processing_id}] Vector store connection test passed: {vs_message}")
                doc_count = org_vector_store.get_document_count()
                print(f"📊 [PROCESSING {processing_id}] Current vector store has {doc_count} documents for org {organization_id or 'default'}")
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
            add_success, add_message = org_vector_store.add_documents(documents)
            
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
            new_doc_count = org_vector_store.get_document_count()
            print(f"📊 [PROCESSING {processing_id}] Vector store now has {new_doc_count} documents for org {organization_id or 'default'}")
        except Exception as vs_error:
            print(f"⚠️ [PROCESSING {processing_id}] Could not get updated document count: {vs_error}")
        
        # Update status
        processing_status[processing_id].update({
            "status": "scanning_duplicates",
            "message": "Scanning for duplicate documents..."
        })
        
        # Scan for duplicates
        print(f"🔍 [PROCESSING {processing_id}] Scanning for duplicates with threshold {request.similarity_threshold}...")
        scan_success, scan_results = org_vector_store.scan_for_duplicates(
            similarity_threshold=request.similarity_threshold,
            update_existing=True
        )
        
        if scan_success:
            print(f"✅ [PROCESSING {processing_id}] Duplicate scan completed successfully")
            
            # Store metadata after successful processing
            try:
                if duplicate_storage_service:
                    metadata = {
                        "total_documents": new_doc_count if 'new_doc_count' in locals() else len(documents),
                        "total_pages": len(documents),
                        "spaces_indexed": request.space_keys,
                        "last_ingestion": datetime.now(timezone.utc).isoformat(),
                        "total_duplicate_pairs": scan_results.get('pairs_found', 0),
                        "pending_duplicate_pairs": scan_results.get('pairs_found', 0),
                        "resolved_duplicate_pairs": 0,
                        "documents_updated": scan_results.get('documents_updated', 0),
                        "processing_id": processing_id
                    }
                    
                    success = duplicate_storage_service.store_organization_metadata(organization_id, metadata)
                    if success:
                        print(f"✅ [PROCESSING {processing_id}] Stored organization metadata")
                    else:
                        print(f"⚠️ [PROCESSING {processing_id}] Failed to store organization metadata")
                        
            except Exception as meta_error:
                print(f"⚠️ [PROCESSING {processing_id}] Metadata storage error: {meta_error}")
            
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
