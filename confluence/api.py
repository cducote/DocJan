"""
Confluence API operations for DocJanitor.
"""
import requests
import json
from config.settings import get_confluence_auth, get_confluence_base_url

def get_available_spaces():
    """
    Get all available Confluence spaces for the authenticated user
    
    Returns:
        list: List of dictionaries containing space information
    """
    try:
        url = f"{get_confluence_base_url()}/rest/api/space"
        params = {
            "limit": 200,  # Get up to 200 spaces
            "expand": "description.plain"
        }
        
        response = requests.get(url, auth=get_confluence_auth(), params=params)
        
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


def extract_page_id_from_url(url):
    """Extract page ID from Confluence URL"""
    if not url:
        return None
    
    # Debug: Print URL to understand format
    print(f"DEBUG: Extracting page ID from URL: {url}")
    
    try:
        # Method 1: Standard viewpage.action URL
        if 'pageId=' in url:
            page_id = url.split('pageId=')[1].split('&')[0]
            print(f"DEBUG: Found pageId in URL: {page_id}")
            return page_id
        
        # Method 2: Modern Confluence URLs with /pages/
        if '/pages/' in url:
            # URL format: https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
            parts = url.split('/pages/')
            if len(parts) > 1:
                page_id = parts[1].split('/')[0]
                print(f"DEBUG: Found page ID in modern URL: {page_id}")
                return page_id
        
        # Method 3: API content URL
        if '/rest/api/content/' in url:
            # URL format: https://domain.atlassian.net/rest/api/content/123456
            parts = url.split('/rest/api/content/')
            if len(parts) > 1:
                page_id = parts[1].split('?')[0].split('/')[0]
                print(f"DEBUG: Found page ID in API URL: {page_id}")
                return page_id
        
        print(f"DEBUG: No page ID found in URL format")
        return None
        
    except Exception as e:
        print(f"DEBUG: Error extracting page ID: {e}")
        return None


def apply_merge_to_confluence(main_doc, similar_doc, merged_content, keep_main=True):
    """Apply the merge to Confluence: update one page, delete the other"""
    try:
        # This would be implemented to handle the actual Confluence operations
        # For now, return a placeholder response
        return True, "Merge operation completed successfully (placeholder implementation)"
        
    except Exception as e:
        return False, f"Error applying merge: {str(e)}"


def load_documents_from_spaces(space_keys, limit_per_space=50):
    """Load documents from specified Confluence spaces"""
    try:
        # This would be implemented to load documents from Confluence
        # For now, return a placeholder response
        return {
            'success': True,
            'total_loaded': 0,
            'message': "Document loading not yet implemented"
        }
        
    except Exception as e:
        return {
            'success': False,
            'total_loaded': 0,
            'message': f"Error loading documents: {str(e)}"
        }


def undo_merge_operation(merge_id):
    """Undo a merge operation"""
    try:
        # This would be implemented to undo merge operations
        # For now, return a placeholder response
        return True, "Undo operation completed successfully (placeholder implementation)"
        
    except Exception as e:
        return False, f"Error undoing merge: {str(e)}"
        return formatted_spaces
        
    except Exception as e:
        print(f"Error fetching available spaces: {str(e)}")
        return []


def get_page_id_by_title(title, space_key="SD"):
    """
    Get page ID by searching for page title in the space
    
    Args:
        title (str): Page title to search for
        space_key (str): Space key to search in
        
    Returns:
        str: Page ID if found, None otherwise
    """
    try:
        # Search for page by title
        url = f"{get_confluence_base_url()}/rest/api/content"
        params = {
            "title": title,
            "spaceKey": space_key,
            "expand": "version"
        }
        
        response = requests.get(url, auth=get_confluence_auth(), params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                page_id = data['results'][0]['id']
                return page_id
        
        print(f"Could not find page by title: {title}")
        return None
        
    except Exception as e:
        print(f"Error searching for page by title: {e}")
        return None


def get_page_version(page_id):
    """
    Get current version of a Confluence page
    
    Args:
        page_id (str): Confluence page ID
        
    Returns:
        int: Current page version number
    """
    try:
        url = f"{get_confluence_base_url()}/rest/api/content/{page_id}"
        response = requests.get(url, auth=get_confluence_auth())
        if response.status_code == 200:
            data = response.json()
            return data.get('version', {}).get('number', 1)
        return None
    except Exception as e:
        print(f"Error getting page version: {str(e)}")
        return None


def update_confluence_page(page_id, new_content, new_title):
    """
    Update a Confluence page with new content
    
    Args:
        page_id (str): Confluence page ID
        new_content (str): New content for the page
        new_title (str): New title for the page
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Get current version
        current_version = get_page_version(page_id)
        if current_version is None:
            return False, "Could not get current page version"
        
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
        
        # Update the page
        url = f"{get_confluence_base_url()}/rest/api/content/{page_id}"
        response = requests.put(
            url, 
            auth=get_confluence_auth(),
            headers={"Content-Type": "application/json"},
            data=json.dumps(update_data)
        )
        
        if response.status_code == 200:
            return True, "Page updated successfully"
        else:
            return False, f"Failed to update page: {response.status_code} - {response.text}"
    
    except Exception as e:
        return False, f"Error updating page: {str(e)}"


def delete_confluence_page(page_id):
    """
    Delete a Confluence page
    
    Args:
        page_id (str): Confluence page ID
        
    Returns:
        tuple: (success, message)
    """
    try:
        url = f"{get_confluence_base_url()}/rest/api/content/{page_id}"
        response = requests.delete(url, auth=get_confluence_auth())
        
        if response.status_code == 204:
            return True, "Page deleted successfully"
        else:
            return False, f"Failed to delete page: {response.status_code} - {response.text}"
    
    except Exception as e:
        return False, f"Error deleting page: {str(e)}"


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


def get_space_name_from_key(space_key):
    """
    Get space name from space key
    
    Args:
        space_key (str): Confluence space key
        
    Returns:
        str: Space name if found, the space key otherwise
    """
    try:
        url = f"{get_confluence_base_url()}/rest/api/space/{space_key}"
        response = requests.get(url, auth=get_confluence_auth())
        
        if response.status_code == 200:
            data = response.json()
            return data.get('name', space_key)
        else:
            return space_key
    except Exception:
        return space_key
