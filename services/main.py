"""
FastAPI Application for Confluence Document Processing Service.
Clean, containerized backend for connecting to Confluence, processing documents,
and genera    try:
        logger.info("� Environment check - OpenAI API Key: ✅ Set" if os.getenv('OPENAI_API_KEY') else "🔑 Environment check - OpenAI API Key: ❌ Missing")
        
        # Get actual configuration values that will be used
        from services.vector_store_service import VectorStoreConfig
        chroma_persist_dir, _ = VectorStoreConfig.from_environment()
        logger.info(f"💾 ChromaDB path (configured): {chroma_persist_dir}")
        logger.info(f"📂 Current working directory: {os.getcwd()}")
        
        # Show absolute path for clarity
        from pathlib import Path
        abs_chroma_path = Path(chroma_persist_dir).resolve()
        logger.info(f"💾 ChromaDB path (absolute): {abs_chroma_path}")
        logger.info(f"📁 ChromaDB exists: {'✅' if abs_chroma_path.exists() else '❌'}")
        
        logger.info("🗄️ Initializing vector store service from environment...")mbeddings.
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
from .confluence_service import ConfluenceService, ConfluenceConfig
from .vector_store_service import VectorStoreService, VectorStoreConfig

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
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances (will be initialized on startup)
confluence_service: Optional[ConfluenceService] = None
vector_store_service: Optional[VectorStoreService] = None

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
    global vector_store_service
    
    # Log startup
    log_startup("main")
    
    try:
        logger.info("� Environment check - OpenAI API Key: ✅ Set" if os.getenv('OPENAI_API_KEY') else "🔑 Environment check - OpenAI API Key: ❌ Missing")
        logger.info(f"�️ Environment check - ChromaDB persist dir: {os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')}")
        logger.info(f"� Current working directory: {os.getcwd()}")
        
        logger.info("🗄️ Initializing vector store service from environment...")
        # Initialize vector store service from environment
        vector_store_service = VectorStoreConfig.create_service_from_env()
        logger.info("✅ Vector store service initialized successfully")
        
        # Test the vector store
        try:
            logger.info("🧪 Testing vector store connection...")
            vs_success, vs_message = vector_store_service.test_connection()
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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    start_time = time.time()
    
    try:
        # Get vector store status
        vs_service = get_vector_store_for_organization()
        vs_connected, vs_message = vs_service.test_connection()
        
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
                    document_count = org_vector_store.get_document_count()
                    print(f"🔍 [CONNECTION-STATUS] Document count for org {organization_id or 'default'}: {document_count}")
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


@app.get("/duplicates")
async def get_duplicates(organization_id: Optional[str] = None) -> List[DuplicatePair]:
    """Get all detected duplicate document pairs for organization."""
    try:
        # Get organization-specific vector store
        org_vector_store = get_vector_store_for_organization(organization_id)
        
        if not org_vector_store:
            raise HTTPException(status_code=400, detail="Vector store not initialized")
        
        duplicates = org_vector_store.get_duplicates()
        return [DuplicatePair(**dup) for dup in duplicates]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get duplicates: {str(e)}")


# Get duplicate summary (fast, just counts)
@app.get("/duplicates/summary")
async def get_duplicate_summary(organization_id: Optional[str] = None):
    """Get duplicate summary without expensive calculations for organization."""
    try:
        # Get organization-specific vector store
        org_vector_store = get_vector_store_for_organization(organization_id)
        
        if not org_vector_store:
            raise HTTPException(status_code=400, detail="Vector store not initialized")
        
        # Get basic document count
        document_count = org_vector_store.get_document_count()
        
        # Count documents that have similar_docs metadata (fast)
        duplicate_count = org_vector_store.get_duplicate_count()
        
        return {
            "total_documents": document_count,
            "duplicate_pairs": duplicate_count,
            "documents_with_duplicates": duplicate_count * 2 if duplicate_count > 0 else 0,
            "potential_merges": duplicate_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get duplicate summary: {str(e)}")


# Clear all data for organization
@app.post("/clear-organization-data")
async def clear_organization_data(request: ConnectionStatusRequest):
    """Clear all documents and cache from the vector store for a specific organization."""
    try:
        organization_id = request.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
            
        print(f"🗑️ [CLEAR] Clearing all data for organization: {organization_id}")
        
        # Get the organization-specific vector store
        vs_service = get_vector_store_for_organization(organization_id)
        
        success, message = vs_service.clear_all_documents()
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        print(f"✅ [CLEAR] Successfully cleared data for organization: {organization_id}")
        return {"success": True, "message": message, "organization_id": organization_id}
        
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
    log_api_request(logger, "GET", f"/merge/documents/{pair_id}", organization_id)
    
    try:
        # Get the organization-specific vector store
        vs_service = get_vector_store_for_organization(organization_id)
        
        # Get the duplicate pair data
        duplicate_pairs = vs_service.get_duplicate_pairs()
        logger.debug(f"Found {len(duplicate_pairs)} duplicate pairs")
        
        # Find the specific pair
        target_pair = None
        for pair in duplicate_pairs:
            if pair['id'] == pair_id:
                target_pair = pair
                break
        
        if not target_pair:
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(logger, f"/merge/documents/{pair_id}", 404, duration_ms)
            raise HTTPException(status_code=404, detail=f"Duplicate pair {pair_id} not found")
        
        logger.info(f"Found target pair: {target_pair['page1']['title']} <-> {target_pair['page2']['title']}")
        
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
        # Get the organization-specific vector store
        vs_service = get_vector_store_for_organization(request.organization_id)
        
        # Get the duplicate pair data
        duplicate_pairs = vs_service.get_duplicate_pairs()
        
        # Find the specific pair
        target_pair = None
        for pair in duplicate_pairs:
            if pair['id'] == request.pair_id:
                target_pair = pair
                break
        
        if not target_pair:
            raise HTTPException(status_code=404, detail=f"Duplicate pair {request.pair_id} not found")
        
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
        # Get the duplicate pair data
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
            user_credentials=request.user_credentials
        )
        
        print(f"🔍 [APPLY_MERGE] apply_merge_to_confluence returned: success={success}, message={message}")
        
        if not success:
            print(f"❌ [APPLY_MERGE] Merge failed: {message}")
            raise HTTPException(status_code=500, detail=message)
        
        # Mark the duplicate pair as resolved in the vector store
        print(f"🔍 [APPLY_MERGE] Marking duplicate pair {request.pair_id} as resolved...")
        try:
            vs_service.mark_pair_as_resolved(request.pair_id)
            print(f"✅ [APPLY_MERGE] Successfully marked pair {request.pair_id} as resolved")
        except Exception as e:
            print(f"⚠️ [APPLY_MERGE] Failed to mark pair as resolved: {e}")
            # Don't fail the entire operation since the merge was successful
        
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
