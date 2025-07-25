"""
Utility functions for DocJanitor application.
"""
from datetime import datetime, timezone
import pytz

class Document:
    """Document class for handling content with metadata"""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}


def format_timestamp_to_est(iso_timestamp):
    """Convert ISO timestamp to readable EST format"""
    try:
        # Parse the ISO timestamp
        if iso_timestamp.endswith('Z'):
            # Remove Z and treat as UTC
            dt = datetime.fromisoformat(iso_timestamp[:-1]).replace(tzinfo=timezone.utc)
        elif '+' in iso_timestamp or iso_timestamp.count('-') > 2:
            # Has timezone info - parse directly
            dt = datetime.fromisoformat(iso_timestamp)
        else:
            # No timezone info - assume it's already in local EST/EDT time
            dt = datetime.fromisoformat(iso_timestamp)
            est = pytz.timezone('US/Eastern')
            # If no timezone, assume it's already in EST/EDT
            dt = est.localize(dt)
        
        # If the datetime has timezone info, convert to EST/EDT
        if dt.tzinfo is not None:
            est = pytz.timezone('US/Eastern')
            dt_est = dt.astimezone(est)
        else:
            # If no timezone info, assume it's already EST/EDT
            dt_est = dt
        
        # Format as readable string
        return dt_est.strftime("%B %d, %Y at %I:%M %p %Z")
    except Exception as e:
        # Fallback to original if parsing fails
        print(f"DEBUG: Error formatting timestamp {iso_timestamp}: {e}")
        return iso_timestamp[:19].replace('T', ' ')


def extract_page_id_from_url(url):
    """Extract the page ID from a Confluence URL"""
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
        
        # Method 4: Wiki display URL
        if '/display/' in url:
            # This format doesn't contain page ID directly, we need to look for it differently
            # URL format: https://domain.atlassian.net/wiki/display/SPACE/Page+Title
            print(f"DEBUG: Display URL format detected, cannot extract page ID directly")
            return None
        
        print(f"DEBUG: No page ID found in URL format")
        return None
        
    except Exception as e:
        print(f"DEBUG: Error extracting page ID: {e}")
        return None


def get_detected_duplicates(space_keys=None):
    """Get all document pairs that have been detected as duplicates"""
    try:
        from models.database import get_document_database
        db = get_document_database()
        
        # Get all documents from ChromaDB
        all_docs = db.get()
        
        if not all_docs['documents']:
            return []
        
        duplicate_pairs = []
        processed_pairs = set()
        
        for i, metadata in enumerate(all_docs['metadatas']):
            similar_docs_str = metadata.get('similar_docs', '')
            
            if not similar_docs_str:
                continue
            
            # Filter by space if specified
            if space_keys:
                doc_space = metadata.get('space_key', '')
                if doc_space not in space_keys:
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
                
                # Create document objects with enhanced metadata
                enhanced_metadata_1 = metadata.copy()
                enhanced_metadata_2 = all_docs['metadatas'][similar_idx].copy()
                
                # Extract space keys from URLs if not already present
                space_key_1 = enhanced_metadata_1.get('space_key', '')
                if not space_key_1:
                    source_url_1 = enhanced_metadata_1.get('source', '')
                    space_key_1 = extract_space_key_from_url(source_url_1) or 'Unknown'
                    enhanced_metadata_1['space_key'] = space_key_1
                
                space_key_2 = enhanced_metadata_2.get('space_key', '')
                if not space_key_2:
                    source_url_2 = enhanced_metadata_2.get('source', '')
                    space_key_2 = extract_space_key_from_url(source_url_2) or 'Unknown'
                    enhanced_metadata_2['space_key'] = space_key_2
                
                # Add space names to metadata
                try:
                    from models.database import get_space_name_from_key
                    enhanced_metadata_1['space_name'] = get_space_name_from_key(space_key_1)
                    enhanced_metadata_2['space_name'] = get_space_name_from_key(space_key_2)
                except ImportError:
                    # Fallback if import fails
                    enhanced_metadata_1['space_name'] = space_key_1 or 'Unknown'
                    enhanced_metadata_2['space_name'] = space_key_2 or 'Unknown'
                
                doc1 = Document(
                    page_content=all_docs['documents'][i],
                    metadata=enhanced_metadata_1
                )
                
                doc2 = Document(
                    page_content=all_docs['documents'][similar_idx],
                    metadata=enhanced_metadata_2
                )
                
                # Calculate actual similarity using embeddings
                try:
                    from models.database import embeddings
                    import numpy as np
                    from sklearn.metrics.pairwise import cosine_similarity
                    
                    # Generate embeddings for both documents
                    embedding1 = embeddings.embed_query(doc1.page_content)
                    embedding2 = embeddings.embed_query(doc2.page_content)
                    
                    # Calculate cosine similarity
                    similarity_matrix = cosine_similarity([embedding1], [embedding2])
                    similarity = float(similarity_matrix[0][0])
                    
                except Exception as e:
                    print(f"Warning: Could not calculate similarity for pair {doc1_id}-{doc2_id}: {e}")
                    # Fall back to a reasonable default based on the fact they were detected as similar
                    similarity = 0.75  # Default similarity score
                
                duplicate_pairs.append({
                    'doc1': doc1,
                    'doc2': doc2,
                    'similarity': similarity,
                    'doc1_id': doc1_id,
                    'doc2_id': doc2_id
                })
        
        return duplicate_pairs
        
    except Exception as e:
        print(f"Error getting detected duplicates: {e}")
        return []
        
    # Check if URL has a pageId parameter (e.g., ?pageId=123456)
    if "pageId=" in url:
        try:
            # Find the pageId parameter and extract the value
            page_id_part = url.split("pageId=")[1]
            # If there are other parameters after pageId, split by &
            if "&" in page_id_part:
                page_id = page_id_part.split("&")[0]
            else:
                page_id = page_id_part
            return page_id
        except Exception as e:
            print(f"Error extracting page ID from URL parameter: {e}")
            return None
    
    # Check if URL has an ID in the path (e.g., /pages/viewpage.action?pageId=123456)
    elif "/pages/" in url:
        try:
            # Find the last segment of the URL path
            path_parts = url.split("/")
            # The page ID should be the last part of the path
            for i in range(len(path_parts)-1, 0, -1):
                if path_parts[i]:  # Skip empty parts
                    potential_id = path_parts[i]
                    # Check if it's numeric (page ID) or likely a title
                    if potential_id.isdigit():
                        return potential_id
                    break
            return None
        except Exception as e:
            print(f"Error extracting page ID from URL path: {e}")
            return None
            
    return None


def extract_space_key_from_url(url):
    """Extract the space key from a Confluence URL"""
    if not url:
        return None
    
    try:
        # Different URL patterns for space keys
        
        # Pattern 1: /display/SPACEKEY/
        if "/display/" in url:
            parts = url.split("/display/")[1].split("/")
            if parts and parts[0]:
                return parts[0]
        
        # Pattern 2: /spaces/SPACEKEY/
        elif "/spaces/" in url:
            parts = url.split("/spaces/")[1].split("/")
            if parts and parts[0]:
                return parts[0]
        
        # Pattern 3: spaceKey=SPACEKEY parameter
        elif "spaceKey=" in url:
            space_key_part = url.split("spaceKey=")[1]
            if "&" in space_key_part:
                return space_key_part.split("&")[0]
            else:
                return space_key_part
    
    except Exception as e:
        print(f"Error extracting space key from URL: {e}")
        
    return None
