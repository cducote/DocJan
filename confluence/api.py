"""
Confluence API operations for Concatly.
"""
import requests
import json
import sys
from pathlib import Path

# Add config directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Import centralized config
    from config.environment import config
    use_centralized_config = True
except ImportError as e:
    print(f"Warning: Could not import centralized config: {e}")
    use_centralized_config = False
    config = None

# Create a simple logger
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

def get_logger(name):
    return logging.getLogger(name)

# Initialize logger
logger = get_logger(__name__)

def get_confluence_auth(user_credentials=None):
    """Get Confluence authentication credentials."""
    logger.info(f"🔍 get_confluence_auth called with user_credentials: {bool(user_credentials)}")
    
    if user_credentials:
        logger.info("✅ Using provided user credentials for Confluence auth")
        logger.info(f"🔍 User credentials keys: {list(user_credentials.keys())}")
        logger.info(f"🔍 Raw user_credentials: {user_credentials}")
        # Use provided user credentials
        username = user_credentials.get('username')
        api_token = user_credentials.get('apiKey') or user_credentials.get('api_token')
        
        if not username or not api_token:
            logger.error("❌ Provided user credentials are incomplete")
            logger.error(f"🔍 Username: {username}, API token: {bool(api_token)}")
            raise ValueError("Provided user credentials are incomplete")
        
        logger.info(f"✅ Successfully using user credentials for username: {username}")
        return (username, api_token)
    
    # Fallback to environment config
    if config:
        logger.info("🔐 Using centralized config for Confluence auth")
        credentials = config.confluence_credentials
        username = credentials['username']
        api_token = credentials['api_token']
        
        if not username or not api_token:
            logger.error("❌ Confluence credentials not configured in environment")
            raise ValueError("Confluence credentials not configured in environment")
        
        return (username, api_token)
    else:
        # Fallback to direct environment variables
        logger.info("🔐 Using direct environment variables for Confluence auth")
        import os
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_KEY') or os.getenv('CONFLUENCE_API_TOKEN')
        
        if not username or not api_token:
            logger.error("❌ Confluence credentials not found in environment variables")
            raise ValueError("Confluence credentials not configured")
        
        return (username, api_token)

def get_confluence_base_url(user_credentials=None):
    """Get Confluence base URL."""
    logger.info(f"🔍 get_confluence_base_url called with user_credentials: {bool(user_credentials)}")
    
    if user_credentials:
        logger.info("✅ Using provided user credentials for Confluence URL")
        logger.info(f"🔍 User credentials keys: {list(user_credentials.keys())}")
        # Use provided user credentials
        base_url = user_credentials.get('baseUrl') or user_credentials.get('base_url')
        if not base_url:
            logger.error("❌ Provided user credentials missing baseUrl")
            logger.error(f"🔍 Available keys in user_credentials: {list(user_credentials.keys())}")
            raise ValueError("Provided user credentials missing baseUrl")
        
        logger.info(f"✅ Successfully using user base URL: {base_url}")
        return base_url
    
    # Fallback to environment config
    if config:
        logger.info("🌐 Using centralized config for Confluence URL")
        base_url = config.confluence_base_url
        if not base_url:
            logger.error("❌ Confluence base URL not configured in environment")
            raise ValueError("Confluence base URL not configured in environment")
        return base_url
    else:
        # Fallback to direct environment variables
        logger.info("🌐 Using direct environment variables for Confluence URL")
        import os
        base_url = os.getenv('CONFLUENCE_BASE_URL')
        if not base_url:
            logger.error("❌ Confluence base URL not found in environment variables")
            raise ValueError("Confluence base URL not configured")
        return base_url

def get_available_spaces(user_credentials=None):
    """
    Get all available Confluence spaces for the authenticated user
    
    Args:
        user_credentials (dict): User's Confluence credentials
        
    Returns:
        list: List of dictionaries containing space information
    """
    try:
        url = f"{get_confluence_base_url(user_credentials)}/rest/api/space"
        params = {
            "limit": 200,  # Get up to 200 spaces
            "expand": "description.plain"
        }
        
        response = requests.get(url, auth=get_confluence_auth(user_credentials), params=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch spaces: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        spaces = data.get('results', [])
        
        # Format spaces for display
        formatted_spaces = []
        for space in spaces:
            space_key = space.get('key', '')
            space_name = space.get('name', 'Unnamed Space')
            space_type = space.get('type', 'unknown')
            description = space.get('description', {}).get('plain', 'No description')
            
            formatted_spaces.append({
                'key': space_key,
                'name': space_name,
                'type': space_type,
                'description': description,
                'display_name': space_name  # Show only space name, not key
            })
        
        # Sort by space name
        formatted_spaces.sort(key=lambda x: x['name'].lower())
        
        print(f"Found {len(formatted_spaces)} available spaces")
        return formatted_spaces
        
    except Exception as e:
        print(f"Error fetching available spaces: {str(e)}")
        return []


def extract_space_key_from_url(url):
    """Extract space key from Confluence URL"""
    if not url:
        return None
    
    try:
        # Modern Confluence URLs: https://domain.atlassian.net/wiki/spaces/SPACE_KEY/pages/...
        if '/wiki/spaces/' in url:
            parts = url.split('/wiki/spaces/')
            if len(parts) > 1:
                space_key = parts[1].split('/')[0]
                logger.info(f"✅ Extracted space key from URL: {space_key}")
                return space_key
        
        logger.warning(f"⚠️ Could not extract space key from URL: {url}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error extracting space key from URL: {e}")
        return None


def extract_page_id_from_url(url):
    """Extract page ID from Confluence URL"""
    if not url:
        logger.warning("⚠️ No URL provided for page ID extraction")
        return None
    
    logger.info(f"🔍 Extracting page ID from URL: {url}")
    
    try:
        # Method 1: Standard viewpage.action URL
        if 'pageId=' in url:
            page_id = url.split('pageId=')[1].split('&')[0]
            logger.info(f"✅ Found pageId in URL: {page_id}")
            return page_id
        
        # Method 2: Modern Confluence URLs with /pages/
        if '/pages/' in url:
            # URL format: https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
            parts = url.split('/pages/')
            if len(parts) > 1:
                page_id = parts[1].split('/')[0]
                logger.info(f"✅ Extracted page ID from modern URL: {page_id}")
                return page_id
                logger.debug(f"✅ Found page ID in modern URL: {page_id}")
                return page_id
        
        # Method 3: API content URL
        if '/rest/api/content/' in url:
            # URL format: https://domain.atlassian.net/rest/api/content/123456
            parts = url.split('/rest/api/content/')
            if len(parts) > 1:
                page_id = parts[1].split('?')[0].split('/')[0]
                logger.debug(f"✅ Found page ID in API URL: {page_id}")
                return page_id
        
        logger.warning(f"⚠️ No page ID found in URL format: {url}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error extracting page ID from {url}: {e}")
        return None


def apply_merge_to_confluence(main_doc, similar_doc, merged_content, keep_main=True, user_credentials=None):
    """Apply the merge to Confluence: update one page, delete the other, and track the operation"""
    try:
        logger.info(f"🔄 Starting Confluence merge operation (keep_main={keep_main})")
        logger.info(f"🔍 User credentials provided: {bool(user_credentials)}")
        if user_credentials:
            logger.info(f"🔍 User credentials keys: {list(user_credentials.keys())}")
            logger.info(f"🔍 Raw user_credentials: {user_credentials}")
        else:
            logger.warning("⚠️ No user credentials provided to apply_merge_to_confluence!")
        
        # Extract page IDs from URLs (using the function defined in this same file)
        logger.info(f"🔍 Main doc metadata: {main_doc.metadata}")
        logger.info(f"🔍 Similar doc metadata: {similar_doc.metadata}")
        
        main_page_id = extract_page_id_from_url(main_doc.metadata.get('source'))
        similar_page_id = extract_page_id_from_url(similar_doc.metadata.get('source'))
        
        # If 'source' is not available, try 'url' 
        if not main_page_id and 'url' in main_doc.metadata:
            main_page_id = extract_page_id_from_url(main_doc.metadata.get('url'))
            
        if not similar_page_id and 'url' in similar_doc.metadata:
            similar_page_id = extract_page_id_from_url(similar_doc.metadata.get('url'))
        
        logger.info(f"📄 Extracted page IDs - Main: {main_page_id}, Similar: {similar_page_id}")
        
        # If URL extraction failed, try to get page ID by title
        if not main_page_id:
            main_title = main_doc.metadata.get('title')
            # Try to extract space from URL first, then fall back to metadata
            main_url = main_doc.metadata.get('source') or main_doc.metadata.get('url')
            main_space = extract_space_key_from_url(main_url) or main_doc.metadata.get('space_key') or main_doc.metadata.get('space', 'SD')
            logger.warning(f"⚠️ Main page ID not found in URL, searching by title: '{main_title}' in space '{main_space}'")
            if main_title:
                main_page_id = get_page_id_by_title(main_title, main_space, user_credentials)
                logger.info(f"📄 Found main page ID by title: {main_page_id}")
        
        if not similar_page_id:
            similar_title = similar_doc.metadata.get('title')
            # Try to extract space from URL first, then fall back to metadata
            similar_url = similar_doc.metadata.get('source') or similar_doc.metadata.get('url')
            similar_space = extract_space_key_from_url(similar_url) or similar_doc.metadata.get('space_key') or similar_doc.metadata.get('space', 'SD')
            logger.warning(f"⚠️ Similar page ID not found in URL, searching by title: '{similar_title}' in space '{similar_space}'")
            if similar_title:
                similar_page_id = get_page_id_by_title(similar_title, similar_space, user_credentials)
                logger.info(f"📄 Found similar page ID by title: {similar_page_id}")
        
        if not main_page_id or not similar_page_id:
            error_msg = f"Could not extract page IDs. Main: {main_page_id}, Similar: {similar_page_id}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        
        # Determine which page to keep and which to delete
        if keep_main:
            keep_page_id = main_page_id
            delete_page_id = similar_page_id
            keep_title = main_doc.metadata.get('title', 'Merged Document')
            delete_title = similar_doc.metadata.get('title', 'Deleted Document')
            keep_url = main_doc.metadata.get('source', '')
            delete_url = similar_doc.metadata.get('source', '')
        else:
            keep_page_id = similar_page_id
            delete_page_id = main_page_id
            keep_title = similar_doc.metadata.get('title', 'Merged Document')
            delete_title = main_doc.metadata.get('title', 'Deleted Document')
            keep_url = similar_doc.metadata.get('source', '')
            delete_url = main_doc.metadata.get('source', '')
        
        logger.info(f"📝 Keep page: '{keep_title}' (ID: {keep_page_id})")
        logger.info(f"🗑️ Delete page: '{delete_title}' (ID: {delete_page_id})")
        
        # Store merge operation BEFORE making changes
        try:
            from models.database import store_merge_operation
            logger.info("💾 Storing merge operation for tracking...")
            store_success, store_message = store_merge_operation(
                keep_page_id, delete_page_id, merged_content, 
                keep_title, delete_title, keep_url, delete_url
            )
            
            if not store_success:
                logger.warning(f"⚠️ Could not store merge operation: {store_message}")
                # Continue anyway since tracking is not critical for the merge itself
        except ImportError:
            logger.warning("⚠️ Could not import store_merge_operation - merge tracking unavailable")
            store_success = False
            store_message = "Merge tracking not available"
        
        # Convert content to Confluence storage format
        logger.info("🔄 Converting merged content to Confluence storage format...")
        confluence_content = convert_markdown_to_confluence_storage(merged_content)
        logger.debug(f"📝 Converted content length: {len(confluence_content)} characters")
        
        # Update the page we're keeping
        logger.info(f"📝 Updating kept page '{keep_title}' (ID: {keep_page_id})...")
        update_success, update_message = update_confluence_page(
            keep_page_id, 
            confluence_content, 
            keep_title,
            user_credentials
        )
        
        if not update_success:
            error_msg = f"Failed to update page: {update_message}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        
        logger.info(f"✅ Successfully updated page '{keep_title}'")
        
        # Delete the other page
        logger.info(f"🗑️ Deleting duplicate page '{delete_title}' (ID: {delete_page_id})...")
        delete_success, delete_message = delete_confluence_page(delete_page_id, user_credentials)
        
        if not delete_success:
            error_msg = f"Updated page but failed to delete duplicate: {delete_message}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        
        logger.info(f"✅ Successfully deleted duplicate page '{delete_title}'")
        
        # Update Chroma database to remove duplicate relationships
        try:
            from models.database import update_chroma_after_merge
            logger.info("💾 Updating ChromaDB after merge...")
            chroma_success, chroma_message = update_chroma_after_merge(main_doc, similar_doc, keep_main)
            
            if not chroma_success:
                # Log the error but don't fail the entire operation since Confluence was updated successfully
                logger.warning(f"⚠️ Confluence merge succeeded but ChromaDB update failed: {chroma_message}")
                success_message = f"Successfully merged documents. Updated '{keep_title}' and deleted duplicate page."
                if store_success:
                    success_message += " Merge operation tracked for undo capability."
                else:
                    success_message += f" Warning: Merge tracking failed - {store_message}"
                logger.info(f"✅ {success_message}")
                return True, success_message
            
            success_message = f"Successfully merged documents. Updated '{keep_title}', deleted duplicate page, and updated database."
            if store_success:
                success_message += " Merge operation tracked for undo capability."
            else:
                success_message += f" Warning: Merge tracking failed - {store_message}"
            
            logger.info(f"✅ {success_message}")
            return True, success_message
            
        except ImportError:
            logger.warning("⚠️ Could not import update_chroma_after_merge - database update unavailable")
            success_message = f"Successfully merged documents. Updated '{keep_title}' and deleted duplicate page."
            logger.info(f"✅ {success_message}")
            return True, success_message
    
    except Exception as e:
        error_msg = f"Error applying merge: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return False, error_msg


def cleanup_orphaned_chroma_records(user_credentials=None):
    """Remove ChromaDB records that reference deleted Confluence pages
    
    Args:
        user_credentials (dict): User's Confluence credentials
    """
    try:
        from models.database import get_document_database
        import requests
        
        # Get database and all current records
        db = get_document_database()
        all_docs = db.get()
        
        doc_ids = all_docs.get('ids', [])
        metadatas = all_docs.get('metadatas', [])
        
        orphaned_ids = []
        
        for i, doc_id in enumerate(doc_ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            source_url = metadata.get('source', '')
            title = metadata.get('title', 'Unknown')
            
            # Extract page ID from document ID or source URL
            page_id = None
            if source_url:
                page_id = extract_page_id_from_url(source_url)
            elif doc_id.startswith('page_'):
                page_id = doc_id[5:]  # Remove 'page_' prefix
            
            if page_id:
                # Check if the page still exists in Confluence
                try:
                    check_url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}"
                    response = requests.get(check_url, auth=get_confluence_auth(user_credentials))
                    
                    if response.status_code == 404:
                        # Page doesn't exist, mark for deletion
                        orphaned_ids.append(doc_id)
                        logger.info(f"🗑️ Found orphaned record: {title} (ID: {doc_id})")
                    elif response.status_code != 200:
                        logger.warning(f"⚠️ Could not verify page {page_id}: HTTP {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error checking page {page_id}: {e}")
        
        # Remove orphaned records
        if orphaned_ids:
            try:
                db.delete(ids=orphaned_ids)
                logger.info(f"✅ Cleaned up {len(orphaned_ids)} orphaned ChromaDB records")
                return len(orphaned_ids)
            except Exception as e:
                logger.error(f"❌ Error deleting orphaned records: {e}")
                return 0
        else:
            logger.info("✅ No orphaned ChromaDB records found")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Error during orphaned records cleanup: {e}", exc_info=True)
        return 0


def load_documents_from_spaces(space_keys, limit_per_space=50, user_credentials=None):
    """Load documents from specified Confluence spaces into ChromaDB
    
    Args:
        space_keys (list): List of space keys to load documents from
        limit_per_space (int): Maximum number of documents to load per space
    
    Returns:
        dict: Results including number of documents loaded and any errors
    """
    try:
        from langchain_community.document_loaders import ConfluenceLoader
        from models.database import get_document_database
        import hashlib
        
        if not space_keys:
            return {
                'success': False,
                'message': 'No spaces specified',
                'total_loaded': 0,
                'spaces_processed': 0
            }
        
        # Get database
        db = get_document_database()
        
        total_loaded = 0
        spaces_processed = 0
        errors = []
        
        for space_key in space_keys:
            try:
                print(f"DEBUG: Loading documents from space {space_key}...")
                
                # Use ConfluenceLoader to get documents from this space
                loader = ConfluenceLoader(
                    url=get_confluence_base_url(user_credentials),
                    username=get_confluence_auth(user_credentials)[0],
                    api_key=get_confluence_auth(user_credentials)[1],
                    space_key=space_key,
                    include_attachments=False,
                    limit=limit_per_space
                )
                
                documents = loader.load()
                print(f"DEBUG: Loaded {len(documents)} documents from space {space_key}")
                
                if documents:
                    # Generate unique document IDs
                    doc_ids = []
                    for doc in documents:
                        # Try to extract page ID from URL for unique identification
                        page_id = extract_page_id_from_url(doc.metadata.get('source', ''))
                        if page_id:
                            doc_id = f"page_{page_id}"
                        else:
                            # Fallback to hash-based ID
                            title = doc.metadata.get('title', 'untitled')
                            doc_id = f"doc_{hashlib.md5(title.encode()).hexdigest()[:8]}"
                        
                        doc_ids.append(doc_id)
                        
                        # Add space key to metadata for easier filtering
                        doc.metadata['space_key'] = space_key
                        doc.metadata['doc_id'] = doc_id
                    
                    # Add documents to ChromaDB (this will overwrite existing ones with same IDs)
                    db.add_documents(documents, ids=doc_ids)
                    total_loaded += len(documents)
                    print(f"DEBUG: Added {len(documents)} documents from {space_key} to ChromaDB")
                
                spaces_processed += 1
                
            except Exception as e:
                error_msg = f"Error loading from space {space_key}: {str(e)}"
                errors.append(error_msg)
                print(f"DEBUG: {error_msg}")
                continue
        
        if errors:
            return {
                'success': False if total_loaded == 0 else True,
                'message': f"Loaded {total_loaded} documents from {spaces_processed} spaces, but encountered {len(errors)} errors",
                'total_loaded': total_loaded,
                'spaces_processed': spaces_processed,
                'errors': errors
            }
        else:
            return {
                'success': True,
                'message': f"Successfully loaded {total_loaded} documents from {spaces_processed} spaces",
                'total_loaded': total_loaded,
                'spaces_processed': spaces_processed
            }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error during document loading: {str(e)}",
            'total_loaded': 0,
            'spaces_processed': 0
        }


def undo_merge_operation(merge_id, user_credentials=None):
    """Undo a merge operation using Confluence native restore capabilities
    
    Args:
        merge_id (str): The ID of the merge operation to undo
        user_credentials (dict): User's Confluence credentials
    """
    try:
        import json
        import os
        from datetime import datetime
        
        # Load merge operations from the JSON file
        merge_file = "merge_operations.json"
        if not os.path.exists(merge_file):
            return False, "No merge operations found - merge history file doesn't exist"
        
        with open(merge_file, 'r') as f:
            merge_operations = json.load(f)
        
        # Find the merge operation
        merge_record = None
        for operation in merge_operations:
            if operation.get('id') == merge_id:
                merge_record = operation
                break
        
        if not merge_record:
            return False, f"Merge operation {merge_id} not found"
        
        if merge_record.get('status') == 'undone':
            return False, "This merge operation has already been undone"
        
        kept_page_id = merge_record['kept_page_id']
        deleted_page_id = merge_record['deleted_page_id']
        kept_title = merge_record['kept_title']
        deleted_title = merge_record['deleted_title']
        
        # Step 1: Get the current version of the kept page and revert to previous version
        print(f"DEBUG: Attempting to revert page {kept_page_id} to previous version")
        current_version = get_page_version(kept_page_id, user_credentials)
        if current_version is None:
            return False, "Could not get current page version"
        
        # Revert to the version before the merge (current - 1)
        previous_version = current_version - 1
        if previous_version < 1:
            return False, "Cannot revert - page is already at version 1"
        
        revert_success, revert_message = restore_confluence_page_version(
            kept_page_id, previous_version, user_credentials
        )
        if not revert_success:
            return False, f"Failed to revert kept page to version {previous_version}: {revert_message}"
        
        print(f"DEBUG: Successfully reverted kept page to version {previous_version}")
        
        # Step 2: Restore the deleted page from trash
        print(f"DEBUG: Attempting to restore deleted page {deleted_page_id} from trash")
        restore_success, restore_message = restore_deleted_confluence_page_from_trash(deleted_page_id)
        if not restore_success:
            return False, f"Failed to restore deleted page: {restore_message}"
        
        print(f"DEBUG: Successfully restored deleted page from trash")
        
        # Step 3: Update merge operation status
        merge_record['status'] = 'undone'
        merge_record['undo_timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Save updated merge operations back to file
        with open(merge_file, 'w') as f:
            json.dump(merge_operations, f, indent=2)
        
        # Step 4: Re-ingest both restored pages to ChromaDB and scan for duplicates
        print("DEBUG: Re-ingesting restored pages to ChromaDB...")
        
        try:
            from langchain_community.document_loaders import ConfluenceLoader
            from models.database import get_document_database
            import hashlib
            
            # Re-load both pages from Confluence and add them back to ChromaDB
            loader = ConfluenceLoader(
                url=get_confluence_base_url(user_credentials),
                username=get_confluence_auth(user_credentials)[0],
                api_key=get_confluence_auth(user_credentials)[1],
                page_ids=[kept_page_id, deleted_page_id],
                include_attachments=False,
                limit=None
            )
            
            restored_documents = loader.load()
            print(f"DEBUG: Loaded {len(restored_documents)} restored documents from Confluence")
            
            # Add the restored documents back to ChromaDB
            if restored_documents:
                db = get_document_database()
                doc_ids = []
                for doc in restored_documents:
                    page_id = extract_page_id_from_url(doc.metadata.get('source', ''))
                    if page_id:
                        doc_id = f"page_{page_id}"
                        doc.metadata['doc_id'] = doc_id
                        doc_ids.append(doc_id)
                    else:
                        # Fallback to hash-based ID
                        title = doc.metadata.get('title', 'untitled')
                        doc_id = f"doc_{hashlib.md5(title.encode()).hexdigest()[:8]}"
                        doc.metadata['doc_id'] = doc_id
                        doc_ids.append(doc_id)
                
                # Add to ChromaDB
                db.add_documents(restored_documents, ids=doc_ids)
                print(f"DEBUG: Added {len(restored_documents)} restored documents to ChromaDB")
            
        except Exception as e:
            print(f"DEBUG: Error re-ingesting restored pages: {e}")
            # Continue anyway - the main undo operation succeeded
        
        # Step 5: Automatically scan for duplicates after undo
        print("DEBUG: Running automatic duplicate detection after undo...")
        try:
            from models.database import scan_for_duplicates
            scan_result = scan_for_duplicates(similarity_threshold=0.65, update_existing=True)
            
            if scan_result.get('success', False):
                pairs_found = scan_result.get('pairs_found', 0)
                docs_updated = scan_result.get('documents_updated', 0)
                print(f"DEBUG: Duplicate scan completed - found {pairs_found} pairs, updated {docs_updated} documents")
                undo_message = f"Merge operation successfully undone. Both original pages '{kept_title}' and '{deleted_title}' have been restored. Automatic duplicate scan found {pairs_found} duplicate pairs."
            else:
                print(f"DEBUG: Duplicate scan failed: {scan_result.get('message', 'Unknown error')}")
                undo_message = f"Merge operation successfully undone. Both original pages '{kept_title}' and '{deleted_title}' have been restored. Note: Automatic duplicate scan encountered an issue - please run manual scan if needed."
            
        except Exception as e:
            print(f"DEBUG: Error during duplicate scan: {e}")
            undo_message = f"Merge operation successfully undone. Both original pages '{kept_title}' and '{deleted_title}' have been restored. Note: Automatic duplicate scan could not be run - please run manual scan if needed."
        
        return True, undo_message
        
    except Exception as e:
        return False, f"Error undoing merge operation: {str(e)}"


def restore_confluence_page_version(page_id, version_number, user_credentials=None):
    """Restore a Confluence page to a specific version
    
    Args:
        page_id (str): Confluence page ID
        version_number (int): Version number to restore to
        user_credentials (dict): User's Confluence credentials
    """
    try:
        print(f"DEBUG: Starting restore of page {page_id} to version {version_number}")
        
        # Get the specific version content
        url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}"
        params = {"expand": "body.storage,version", "version": version_number}
        response = requests.get(url, auth=get_confluence_auth(user_credentials), params=params)
        
        if response.status_code != 200:
            return False, f"Could not get version {version_number}: {response.status_code} - {response.text}"
        
        version_data = response.json()
        retrieved_version = version_data.get('version', {}).get('number')
        print(f"DEBUG: Retrieved version {retrieved_version} for page {page_id}")
        
        # Verify we got the right version
        if retrieved_version != version_number:
            return False, f"Retrieved version {retrieved_version} instead of {version_number}"
        
        # Get current version
        current_version = get_page_version(page_id, user_credentials)
        if current_version is None:
            return False, "Could not get current page version"
        
        print(f"DEBUG: Current page version is {current_version}, restoring to version {version_number}")
        
        # Prepare update data with explicit confirmation that we want to revert
        update_data = {
            "version": {
                "number": current_version + 1,
                "message": f"Reverted to version {version_number} via Concatly undo operation"
            },
            "title": version_data.get('title'),
            "type": "page",
            "body": {
                "storage": {
                    "value": version_data['body']['storage']['value'],
                    "representation": "storage"
                }
            }
        }
        
        # Update the page with proper headers
        update_url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"DEBUG: Updating page {page_id} to new version {current_version + 1} with content from version {version_number}")
        response = requests.put(
            update_url, 
            auth=get_confluence_auth(user_credentials),
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            new_version = response.json().get('version', {}).get('number', 'unknown')
            print(f"DEBUG: Successfully updated page to version {new_version}")
            return True, f"Page restored to version {version_number} successfully (new version: {new_version})"
        else:
            print(f"DEBUG: Failed to update page: {response.status_code} - {response.text}")
            return False, f"Failed to restore page: {response.status_code} - {response.text}"
    
    except Exception as e:
        print(f"DEBUG: Exception in restore_confluence_page_version: {e}")
        return False, f"Error restoring page version: {str(e)}"


def restore_deleted_confluence_page_from_trash(page_id, user_credentials=None):
    """Restore a deleted Confluence page from trash without checking for duplicates
    
    Args:
        page_id (str): Confluence page ID
        user_credentials (dict): User's Confluence credentials
    """
    try:
        # First, check if the page exists in trash
        check_url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}?status=trashed&expand=body.storage"
        check_response = requests.get(check_url, auth=get_confluence_auth(user_credentials))
        
        if check_response.status_code != 200:
            return False, f"Page {page_id} not found in trash: {check_response.status_code} - {check_response.text}"
        
        # Get page data
        page_data = check_response.json()
        page_title = page_data.get('title', 'Restored Page')
        page_content = page_data.get('body', {}).get('storage', {}).get('value', '')
        
        # Method 1: Try the standard restore endpoint with confirmation
        restore_url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}/restore"
        
        # Add headers to indicate we're programmatically confirming the restore
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Some Confluence instances may require a body with confirmation
        restore_data = {
            "confirm": True,
            "restoreMode": "full"  # Restore the full page
        }
        
        response = requests.post(
            restore_url, 
            auth=get_confluence_auth(user_credentials),
            headers=headers,
            json=restore_data
        )
        
        restore_success = False
        if response.status_code == 200:
            restore_success = True
        else:
            # Method 2: If that fails, try without the body (some versions don't need it)
            response = requests.post(restore_url, auth=get_confluence_auth(user_credentials), headers=headers)
            
            if response.status_code == 200:
                restore_success = True
            else:
                # Method 3: Try using PUT to change the status from trashed to current
                update_url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}"
                current_version = page_data.get('version', {}).get('number', 1)
                
                # Update the page status
                update_data = {
                    "version": {
                        "number": current_version + 1
                    },
                    "title": page_title,
                    "type": "page",
                    "status": "current",  # Change from trashed to current
                    "body": {
                        "storage": {
                            "value": page_content,
                            "representation": "storage"
                        }
                    }
                }
                
                response = requests.put(
                    update_url,
                    auth=get_confluence_auth(user_credentials),
                    headers=headers,
                    json=update_data
                )
                
                if response.status_code == 200:
                    restore_success = True
        
        if not restore_success:
            return False, f"All restore methods failed. Last error: {response.status_code} - {response.text}"
        
        print(f"DEBUG: Successfully restored page '{page_title}' without duplicate checking")
        return True, "Page restored from trash successfully"
        
    except Exception as e:
        return False, f"Error restoring page from trash: {str(e)}"


def get_page_id_by_title(title, space_key="SD", user_credentials=None):
    """
    Get page ID by searching for page title in the space
    
    Args:
        title (str): Page title to search for
        space_key (str): Space key to search in
        user_credentials (dict): User's Confluence credentials
        
    Returns:
        str: Page ID if found, None otherwise
    """
    try:
        logger.info(f"🔍 Searching for page '{title}' in space '{space_key}'")
        
        # Search for page by title
        url = f"{get_confluence_base_url(user_credentials)}/rest/api/content"
        params = {
            "title": title,
            "spaceKey": space_key,
            "expand": "version"
        }
        
        response = requests.get(url, auth=get_confluence_auth(user_credentials), params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                page_id = data['results'][0]['id']
                logger.info(f"✅ Found page '{title}' with ID: {page_id}")
                return page_id
        
        logger.warning(f"⚠️ Could not find page by title: '{title}' in space '{space_key}'")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error searching for page by title '{title}': {e}", exc_info=True)
        return None


def get_page_version(page_id, user_credentials=None):
    """
    Get current version of a Confluence page
    
    Args:
        page_id (str): Confluence page ID
        user_credentials (dict): User's Confluence credentials
        
    Returns:
        int: Current page version number
    """
    try:
        url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}"
        response = requests.get(url, auth=get_confluence_auth(user_credentials))
        if response.status_code == 200:
            data = response.json()
            return data.get('version', {}).get('number', 1)
        return None
    except Exception as e:
        logger.error(f"❌ Error getting page version: {str(e)}", exc_info=True)
        return None


def update_confluence_page(page_id, new_content, new_title, user_credentials=None):
    """
    Update a Confluence page with new content
    
    Args:
        page_id (str): Confluence page ID
        new_content (str): New content for the page
        new_title (str): New title for the page
        user_credentials (dict): User's Confluence credentials
        
    Returns:
        tuple: (success, message)
    """
    try:
        logger.info(f"📝 Updating Confluence page '{new_title}' (ID: {page_id})")
        
        # Get current version
        current_version = get_page_version(page_id, user_credentials)
        if current_version is None:
            logger.error(f"❌ Could not get current version for page {page_id}")
            return False, "Could not get current page version"
        
        logger.debug(f"📄 Current page version: {current_version}")
        
        # Prepare update payload
        update_data = {
            "version": {
                "number": current_version + 1
            },
            "title": new_title,
            "type": "page",
            "body": {
                "storage": {
                    "value": new_content,
                    "representation": "storage"
                }
            }
        }
        
        logger.debug(f"📦 Update payload prepared for version {current_version + 1}")
        
        # Update the page
        url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}"
        response = requests.put(
            url, 
            auth=get_confluence_auth(user_credentials),
            headers={"Content-Type": "application/json"},
            data=json.dumps(update_data)
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully updated page '{new_title}' (ID: {page_id})")
            return True, "Page updated successfully"
        else:
            error_msg = f"Failed to update page: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    except Exception as e:
        error_msg = f"Error updating page: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return False, error_msg


def delete_confluence_page(page_id, user_credentials=None):
    """
    Delete a Confluence page
    
    Args:
        page_id (str): Confluence page ID
        user_credentials (dict): User's Confluence credentials
        
    Returns:
        tuple: (success, message)
    """
    try:
        logger.info(f"🗑️ Deleting Confluence page (ID: {page_id})")
        
        url = f"{get_confluence_base_url(user_credentials)}/rest/api/content/{page_id}"
        response = requests.delete(url, auth=get_confluence_auth(user_credentials))
        
        if response.status_code == 204:
            logger.info(f"✅ Successfully deleted page (ID: {page_id})")
            return True, "Page deleted successfully"
        else:
            error_msg = f"Failed to delete page: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    except Exception as e:
        error_msg = f"Error deleting page: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return False, error_msg


def convert_markdown_to_confluence_storage(content):
    """
    Convert content to Confluence storage format
    
    Args:
        content (str): Content to convert
        
    Returns:
        str: Content in Confluence storage format
    """
    # Since the AI now generates HTML directly, we mainly need to ensure it's clean
    storage_content = content.strip()
    
    # If the content doesn't already have proper HTML structure, wrap it
    if not storage_content.startswith('<'):
        # Wrap plain text in paragraph tags
        storage_content = f"<p>{storage_content}</p>"
    
    # Ensure proper paragraph structure for any remaining plain text
    # Replace double newlines with proper paragraph breaks
    storage_content = storage_content.replace('\n\n', '</p><p>')
    
    # Clean up any remaining single newlines that might break formatting
    storage_content = storage_content.replace('\n', ' ')
    
    return storage_content


def get_space_name_from_key(space_key, user_credentials=None):
    """
    Get space name from space key
    
    Args:
        space_key (str): Confluence space key
        user_credentials (dict): User's Confluence credentials
        
    Returns:
        str: Space name if found, the space key otherwise
    """
    try:
        url = f"{get_confluence_base_url(user_credentials)}/rest/api/space/{space_key}"
        response = requests.get(url, auth=get_confluence_auth(user_credentials))
        
        if response.status_code == 200:
            data = response.json()
            return data.get('name', space_key)
        else:
            return space_key
    except Exception:
        return space_key
