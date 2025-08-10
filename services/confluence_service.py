"""
Confluence Service - Core business logic for connecting to Confluence and processing documents.
Extracted from Streamlit app for containerized deployment.
"""
import os
import requests
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from langchain_community.document_loaders import ConfluenceLoader
from langchain.schema import Document


class ConfluenceService:
    """
    Core Confluence operations service.
    Handles authentication, space discovery, page loading, and content processing.
    """
    
    def __init__(self, base_url: str, username: str, api_token: str):
        """
        Initialize Confluence service with credentials.
        
        Args:
            base_url: Confluence base URL (e.g., https://company.atlassian.net/wiki)
            username: Confluence username/email
            api_token: Confluence API token
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.auth = (username, api_token)
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to Confluence with provided credentials.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            test_url = f"{self.base_url}/rest/api/user/current"
            response = requests.get(test_url, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                display_name = user_data.get('displayName', 'Unknown User')
                return True, f"Successfully connected as {display_name}"
            else:
                return False, f"Authentication failed: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "Connection timeout - check your Confluence URL"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_all_accessible_spaces(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Get all Confluence spaces accessible to the authenticated user.
        
        Returns:
            Tuple of (success, spaces_list, message)
        """
        try:
            url = f"{self.base_url}/rest/api/space"
            params = {
                "limit": 200,  # Get up to 200 spaces
                "expand": "description.plain,description.view"
            }
            
            response = requests.get(url, auth=self.auth, params=params)
            
            if response.status_code != 200:
                return False, [], f"Failed to fetch spaces: {response.status_code} - {response.text}"
            
            data = response.json()
            spaces = data.get('results', [])
            
            # Format spaces for consistent output
            formatted_spaces = []
            for space in spaces:
                space_key = space.get('key', '')
                space_name = space.get('name', 'Unnamed Space')
                space_type = space.get('type', 'unknown')
                
                # Handle description field - it can be a string, dict, or None
                description_field = space.get('description', {})
                if isinstance(description_field, dict):
                    description = description_field.get('plain', '') or description_field.get('value', '') or 'No description'
                elif isinstance(description_field, str):
                    description = description_field
                else:
                    description = 'No description'
                
                # Ensure description is always a string
                if not isinstance(description, str):
                    description = 'No description'
                
                formatted_spaces.append({
                    'key': space_key,
                    'name': space_name,
                    'type': space_type,
                    'description': description,
                    'display_name': space_name
                })
            
            # Sort by space name
            formatted_spaces.sort(key=lambda x: x['name'].lower())
            
            message = f"Found {len(formatted_spaces)} accessible spaces"
            return True, formatted_spaces, message
            
        except Exception as e:
            return False, [], f"Error fetching spaces: {str(e)}"
    
    def load_all_pages_from_spaces(self, space_keys: List[str], limit_per_space: Optional[int] = None) -> Tuple[bool, List[Document], str]:
        """
        Load all pages from specified Confluence spaces with efficient logic.
        
        Args:
            space_keys: List of space keys to load from
            limit_per_space: Optional limit per space (None for no limit)
            
        Returns:
            Tuple of (success, documents_list, message)
        """
        try:
            if not space_keys:
                return False, [], "No spaces specified"
            
            all_documents = []
            total_loaded = 0
            spaces_processed = 0
            errors = []
            
            for space_key in space_keys:
                try:
                    print(f"Loading documents from space {space_key}...")
                    
                    # Use ConfluenceLoader for efficient document loading
                    # Only pass limit if it's not None to avoid comparison issues
                    loader_kwargs = {
                        'url': self.base_url,
                        'username': self.username,
                        'api_key': self.api_token,
                        'space_key': space_key,
                        'include_attachments': False
                    }
                    
                    # Only add limit if it's specified (not None)
                    if limit_per_space is not None:
                        loader_kwargs['limit'] = limit_per_space
                    
                    loader = ConfluenceLoader(**loader_kwargs)
                    
                    documents = loader.load()
                    print(f"Loaded {len(documents)} documents from space {space_key}")
                    
                    # Process and enhance document metadata
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
                        doc.metadata.update({
                            'space_key': space_key,
                            'doc_id': doc_id,
                            'processed_at': datetime.now(timezone.utc).isoformat(),
                            'content_length': len(doc.page_content),
                            'space_name': space_key  # Will be updated if we can get actual space name
                        })
                    
                    all_documents.extend(documents)
                    total_loaded += len(documents)
                    spaces_processed += 1
                    
                except Exception as e:
                    error_msg = f"Error loading from space {space_key}: {str(e)}"
                    errors.append(error_msg)
                    print(f"ERROR: {error_msg}")
                    continue
            
            # Prepare result message
            if errors:
                message = f"Loaded {total_loaded} documents from {spaces_processed} spaces, but encountered {len(errors)} errors: {'; '.join(errors[:3])}"
                success = total_loaded > 0
            else:
                message = f"Successfully loaded {total_loaded} documents from {spaces_processed} spaces"
                success = True
            
            return success, all_documents, message
            
        except Exception as e:
            return False, [], f"Error during document loading: {str(e)}"
    
    def get_space_name_from_key(self, space_key: str) -> str:
        """
        Get space name from space key.
        
        Args:
            space_key: Confluence space key
            
        Returns:
            Space name if found, space key otherwise
        """
        try:
            url = f"{self.base_url}/rest/api/space/{space_key}"
            response = requests.get(url, auth=self.auth, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('name', space_key)
            else:
                return space_key
        except Exception:
            return space_key
    
    def _extract_page_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract page ID from Confluence URL.
        
        Args:
            url: Confluence page URL
            
        Returns:
            Page ID if found, None otherwise
        """
        if not url:
            return None
        
        try:
            # Method 1: Standard viewpage.action URL
            if 'pageId=' in url:
                page_id = url.split('pageId=')[1].split('&')[0]
                return page_id
            
            # Method 2: Modern Confluence URLs with /pages/
            if '/pages/' in url:
                parts = url.split('/pages/')
                if len(parts) > 1:
                    page_id = parts[1].split('/')[0]
                    return page_id
            
            # Method 3: API content URL
            if '/rest/api/content/' in url:
                parts = url.split('/rest/api/content/')
                if len(parts) > 1:
                    page_id = parts[1].split('?')[0].split('/')[0]
                    return page_id
            
            return None
            
        except Exception as e:
            print(f"Error extracting page ID from {url}: {e}")
            return None


class ConfluenceConfig:
    """Configuration helper for Confluence service."""
    
    @staticmethod
    def from_environment() -> Tuple[str, str, str]:
        """
        Load Confluence configuration from environment variables.
        
        Returns:
            Tuple of (base_url, username, api_token)
            
        Raises:
            ValueError: If required environment variables are missing
        """
        base_url = os.getenv('CONFLUENCE_BASE_URL')
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if not all([base_url, username, api_token]):
            missing = []
            if not base_url:
                missing.append('CONFLUENCE_BASE_URL')
            if not username:
                missing.append('CONFLUENCE_USERNAME')
            if not api_token:
                missing.append('CONFLUENCE_API_TOKEN')
            
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return base_url, username, api_token
    
    @staticmethod
    def create_service_from_env() -> ConfluenceService:
        """
        Create a ConfluenceService instance from environment variables.
        
        Returns:
            Configured ConfluenceService instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        base_url, username, api_token = ConfluenceConfig.from_environment()
        return ConfluenceService(base_url, username, api_token)