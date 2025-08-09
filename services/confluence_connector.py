"""
Confluence Connector Service - Core business logic for Confluence integration.
Extracted from the original Streamlit app for containerization.
"""
import requests
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from langchain_community.document_loaders import ConfluenceLoader
from langchain_core.documents import Document
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ConfluenceCredentials:
    """Confluence authentication credentials."""
    base_url: str
    username: str
    api_token: str
    

@dataclass
class ConfluenceSpace:
    """Confluence space information."""
    key: str
    name: str
    type: str
    description: str = ""


@dataclass
class IngestionResult:
    """Result of document ingestion operation."""
    success: bool
    message: str
    total_loaded: int = 0
    spaces_processed: int = 0
    errors: List[str] = None


class ConfluenceConnector:
    """
    Core Confluence connector for reading spaces and pages.
    Handles authentication, space discovery, and document loading.
    """
    
    def __init__(self, credentials: ConfluenceCredentials):
        """Initialize with Confluence credentials."""
        self.credentials = credentials
        self.session = requests.Session()
        self.session.auth = (credentials.username, credentials.api_token)
        
    def test_connection(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Test connection to Confluence with provided credentials.
        
        Returns:
            Tuple of (success, error_message, user_info)
        """
        try:
            # Clean up base URL
            clean_base_url = self.credentials.base_url.rstrip('/')
            
            # Test connection by getting current user info
            test_url = f"{clean_base_url}/rest/api/user/current"
            
            logger.info(f"Testing Confluence connection to: {test_url}")
            
            response = self.session.get(
                test_url,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Concatly/1.0',
                },
                timeout=15
            )
            
            if not response.ok:
                error_msg = f"HTTP {response.status_code}"
                if response.status_code == 401:
                    error_msg = "Invalid username or API token"
                elif response.status_code == 404:
                    error_msg = "Invalid base URL - Confluence API not found"
                elif response.status_code == 403:
                    error_msg = "Access denied - check permissions"
                elif response.status_code >= 500:
                    error_msg = f"Server error ({response.status_code}) - Confluence instance may be down"
                
                return False, error_msg, None
            
            user_info = response.json()
            logger.info(f"Connection successful for user: {user_info.get('displayName', 'Unknown')}")
            
            return True, "Connection successful", {
                'username': user_info.get('username'),
                'displayName': user_info.get('displayName'),
                'emailAddress': user_info.get('emailAddress'),
            }
            
        except requests.exceptions.Timeout:
            return False, "Connection timeout (15s) - check your base URL", None
        except requests.exceptions.ConnectionError as e:
            if 'ENOTFOUND' in str(e):
                return False, "DNS lookup failed - check your base URL domain", None
            elif 'ECONNREFUSED' in str(e):
                return False, "Connection refused - server may be down or URL incorrect", None
            else:
                return False, f"Network error - {str(e)}", None
        except Exception as e:
            logger.error(f"Confluence connection test failed: {e}")
            return False, f"Connection test failed: {str(e)}", None
    
    def get_all_spaces(self) -> List[ConfluenceSpace]:
        """
        Get all available Confluence spaces for the authenticated user.
        
        Returns:
            List of ConfluenceSpace objects
        """
        try:
            url = f"{self.credentials.base_url.rstrip('/')}/rest/api/space"
            params = {
                "limit": 200,  # Get up to 200 spaces
                "expand": "description.plain"
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch spaces: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            spaces = data.get('results', [])
            
            # Convert to ConfluenceSpace objects
            confluence_spaces = []
            for space in spaces:
                confluence_spaces.append(ConfluenceSpace(
                    key=space.get('key', ''),
                    name=space.get('name', 'Unnamed Space'),
                    type=space.get('type', 'unknown'),
                    description=space.get('description', {}).get('plain', 'No description')
                ))
            
            # Sort by space name
            confluence_spaces.sort(key=lambda x: x.name.lower())
            
            logger.info(f"Found {len(confluence_spaces)} available spaces")
            return confluence_spaces
            
        except Exception as e:
            logger.error(f"Error fetching available spaces: {str(e)}")
            return []
    
    def get_pages_from_spaces(self, space_keys: List[str], limit_per_space: Optional[int] = None) -> List[Document]:
        """
        Load all pages from specified Confluence spaces.
        
        Args:
            space_keys: List of space keys to load documents from
            limit_per_space: Maximum number of documents to load per space (None for unlimited)
        
        Returns:
            List of Document objects with content and metadata
        """
        if not space_keys:
            logger.warning("No spaces specified for document loading")
            return []
        
        all_documents = []
        
        for space_key in space_keys:
            try:
                logger.info(f"Loading documents from space: {space_key}")
                
                # Use ConfluenceLoader to get documents from this space
                loader = ConfluenceLoader(
                    url=self.credentials.base_url,
                    username=self.credentials.username,
                    api_key=self.credentials.api_token,
                    space_key=space_key,
                    include_attachments=False,
                    limit=limit_per_space
                )
                
                documents = loader.load()
                logger.info(f"Loaded {len(documents)} documents from space {space_key}")
                
                # Add space metadata and generate doc IDs
                for doc in documents:
                    # Extract page ID from URL for unique identification
                    page_id = self._extract_page_id_from_url(doc.metadata.get('source', ''))
                    if page_id:
                        doc_id = f"page_{page_id}"
                    else:
                        # Fallback to hash-based ID
                        title = doc.metadata.get('title', 'untitled')
                        doc_id = f"doc_{hashlib.md5(title.encode()).hexdigest()[:8]}"
                    
                    # Enhance metadata
                    doc.metadata['space_key'] = space_key
                    doc.metadata['doc_id'] = doc_id
                    doc.metadata['source_type'] = 'confluence'
                
                all_documents.extend(documents)
                
            except Exception as e:
                logger.error(f"Error loading from space {space_key}: {str(e)}")
                continue
        
        logger.info(f"Total documents loaded: {len(all_documents)}")
        return all_documents
    
    def _extract_page_id_from_url(self, url: str) -> Optional[str]:
        """Extract page ID from Confluence URL."""
        if not url:
            return None
        
        try:
            # Method 1: Standard viewpage.action URL
            if 'pageId=' in url:
                page_id = url.split('pageId=')[1].split('&')[0]
                return page_id
            
            # Method 2: Modern Confluence URLs with /pages/
            if '/pages/' in url:
                # URL format: https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
                parts = url.split('/pages/')
                if len(parts) > 1:
                    page_id = parts[1].split('/')[0]
                    return page_id
            
            # Method 3: API content URL
            if '/rest/api/content/' in url:
                # URL format: https://domain.atlassian.net/rest/api/content/123456
                parts = url.split('/rest/api/content/')
                if len(parts) > 1:
                    page_id = parts[1].split('?')[0].split('/')[0]
                    return page_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting page ID from URL {url}: {e}")
            return None


class ConfluenceService:
    """
    High-level service for Confluence operations.
    Orchestrates connector and vector store operations.
    """
    
    def __init__(self, vector_store):
        """Initialize with a vector store instance."""
        self.vector_store = vector_store
        self.connector = None
    
    def connect(self, credentials: ConfluenceCredentials) -> Tuple[bool, str, Optional[Dict]]:
        """
        Connect to Confluence with provided credentials.
        
        Returns:
            Tuple of (success, message, user_info)
        """
        self.connector = ConfluenceConnector(credentials)
        return self.connector.test_connection()
    
    def get_available_spaces(self) -> List[ConfluenceSpace]:
        """Get all available spaces."""
        if not self.connector:
            raise ValueError("Not connected to Confluence. Call connect() first.")
        
        return self.connector.get_all_spaces()
    
    def ingest_all_spaces(self, limit_per_space: Optional[int] = None) -> IngestionResult:
        """
        Ingest all accessible spaces into the vector store.
        
        Args:
            limit_per_space: Maximum number of documents to load per space
        
        Returns:
            IngestionResult with success status and details
        """
        if not self.connector:
            return IngestionResult(
                success=False,
                message="Not connected to Confluence. Call connect() first."
            )
        
        try:
            # Get all available spaces
            spaces = self.connector.get_all_spaces()
            if not spaces:
                return IngestionResult(
                    success=False,
                    message="No spaces found or accessible"
                )
            
            space_keys = [space.key for space in spaces]
            logger.info(f"Starting ingestion for {len(space_keys)} spaces: {space_keys}")
            
            # Load documents from all spaces
            documents = self.connector.get_pages_from_spaces(space_keys, limit_per_space)
            
            if not documents:
                return IngestionResult(
                    success=False,
                    message="No documents found in any space"
                )
            
            # Store in vector database
            doc_ids = [doc.metadata['doc_id'] for doc in documents]
            self.vector_store.add_documents(documents, ids=doc_ids)
            
            logger.info(f"Successfully ingested {len(documents)} documents from {len(spaces)} spaces")
            
            return IngestionResult(
                success=True,
                message=f"Successfully ingested {len(documents)} documents from {len(spaces)} spaces",
                total_loaded=len(documents),
                spaces_processed=len(spaces)
            )
            
        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}")
            return IngestionResult(
                success=False,
                message=f"Error during ingestion: {str(e)}"
            )
    
    def ingest_specific_spaces(self, space_keys: List[str], limit_per_space: Optional[int] = None) -> IngestionResult:
        """
        Ingest specific spaces into the vector store.
        
        Args:
            space_keys: List of space keys to ingest
            limit_per_space: Maximum number of documents to load per space
        
        Returns:
            IngestionResult with success status and details
        """
        if not self.connector:
            return IngestionResult(
                success=False,
                message="Not connected to Confluence. Call connect() first."
            )
        
        try:
            logger.info(f"Starting ingestion for specific spaces: {space_keys}")
            
            # Load documents from specified spaces
            documents = self.connector.get_pages_from_spaces(space_keys, limit_per_space)
            
            if not documents:
                return IngestionResult(
                    success=False,
                    message="No documents found in specified spaces"
                )
            
            # Store in vector database
            doc_ids = [doc.metadata['doc_id'] for doc in documents]
            self.vector_store.add_documents(documents, ids=doc_ids)
            
            logger.info(f"Successfully ingested {len(documents)} documents from {len(space_keys)} spaces")
            
            return IngestionResult(
                success=True,
                message=f"Successfully ingested {len(documents)} documents from {len(space_keys)} spaces",
                total_loaded=len(documents),
                spaces_processed=len(space_keys)
            )
            
        except Exception as e:
            logger.error(f"Error during specific space ingestion: {str(e)}")
            return IngestionResult(
                success=False,
                message=f"Error during ingestion: {str(e)}"
            )
