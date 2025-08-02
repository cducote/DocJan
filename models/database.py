"""
Database operations and management for DocJanitor.
"""
import os
import sys

# Fix for SQLite3 version compatibility on cloud platforms
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config.settings import CHROMA_PERSIST_DIRECTORY

# Setup embeddings and Chroma vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Main document database
db = Chroma(persist_directory=CHROMA_PERSIST_DIRECTORY, embedding_function=embeddings)

# Merge tracking collection
MERGE_COLLECTION_NAME = "merge_operations"
try:
    merge_collection = Chroma(
        collection_name=MERGE_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIRECTORY,
        embedding_function=embeddings
    )
except Exception as e:
    print(f"Warning: Could not initialize merge tracking collection: {e}")
    merge_collection = None


def get_document_database():
    """
    Get the main document database
    
    Returns:
        Chroma: The document database instance
    """
    return db


def get_merge_collection():
    """
    Get the merge tracking collection
    
    Returns:
        Chroma: The merge tracking collection instance
    """
    return merge_collection


def store_merge_operation(kept_page_id, deleted_page_id, merged_content, kept_title, deleted_title, kept_url="", deleted_url=""):
    """
    Store a merge operation record for tracking and undo capability
    
    Args:
        kept_page_id (str): ID of the page that was kept
        deleted_page_id (str): ID of the page that was deleted
        merged_content (str): Content of the merged document
        kept_title (str): Title of the kept page
        deleted_title (str): Title of the deleted page
        kept_url (str): URL of the kept page
        deleted_url (str): URL of the deleted page
        
    Returns:
        dict: Merge operation record
    """
    try:
        import json
        import uuid
        from datetime import datetime
        
        # Generate unique ID for this merge operation
        merge_id = str(uuid.uuid4())
        
        # Create record
        timestamp = datetime.utcnow().isoformat() + 'Z'  # UTC with Z suffix
        
        merge_record = {
            "id": merge_id,
            "kept_page_id": kept_page_id,
            "deleted_page_id": deleted_page_id,
            "kept_title": kept_title,
            "deleted_title": deleted_title,
            "timestamp": timestamp,
            "status": "completed",  # Initial status
            "merged_content": merged_content,
            "kept_url": kept_url,
            "deleted_url": deleted_url
        }
        
        # Try to load existing merge operations
        merge_operations = []
        merge_file = "merge_operations.json"
        
        if os.path.exists(merge_file):
            try:
                with open(merge_file, 'r') as f:
                    merge_operations = json.load(f)
            except:
                merge_operations = []
        
        # Add new operation
        merge_operations.append(merge_record)
        
        # Save back to file
        with open(merge_file, 'w') as f:
            json.dump(merge_operations, f, indent=2)
        
        return True, f"Merge operation stored with ID: {merge_id}"
    
    except Exception as e:
        print(f"Error storing merge operation: {str(e)}")
        return False, f"Failed to store merge operation: {str(e)}"


def get_recent_merges(limit=20):
    """
    Get recent merge operations
    
    Args:
        limit (int): Maximum number of operations to return
        
    Returns:
        list: Recent merge operations
    """
    try:
        import json
        
        merge_file = "merge_operations.json"
        
        if not os.path.exists(merge_file):
            return []
        
        with open(merge_file, 'r') as f:
            merge_operations = json.load(f)
        
        # Sort by timestamp (newest first)
        merge_operations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return up to limit entries
        return merge_operations[:limit]
    
    except Exception as e:
        print(f"Error getting merge operations: {str(e)}")
        return []


def update_merge_status(merge_id, new_status):
    """
    Update the status of a merge operation
    
    Args:
        merge_id (str): ID of the merge operation
        new_status (str): New status (e.g., 'completed', 'undone')
        
    Returns:
        bool: Success or failure
    """
    try:
        import json
        
        merge_file = "merge_operations.json"
        
        if not os.path.exists(merge_file):
            return False
        
        # Load operations
        with open(merge_file, 'r') as f:
            merge_operations = json.load(f)
        
        # Find and update operation
        for operation in merge_operations:
            if operation.get('id') == merge_id:
                operation['status'] = new_status
                
                # Write back
                with open(merge_file, 'w') as f:
                    json.dump(merge_operations, f, indent=2)
                
                return True
        
        return False
    
    except Exception as e:
        print(f"Error updating merge status: {str(e)}")
        return False


def scan_for_duplicates(similarity_threshold=0.65, update_existing=True):
    """
    Scan all documents in ChromaDB for duplicates and update their similarity relationships.
    This can be called after undoing merges or when new content is added.
    
    Args:
        similarity_threshold (float): Threshold for considering documents similar (default: 0.65)
        update_existing (bool): Whether to update existing similarity relationships (default: True)
    
    Returns:
        dict: Results including number of pairs found and updated
    """
    try:
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        import pytz
        from datetime import datetime
        from utils.helpers import Document
        
        # Get all documents from ChromaDB
        all_docs = db.get()
        
        if not all_docs['documents'] or len(all_docs['documents']) < 2:
            return {
                'success': True,
                'pairs_found': 0,
                'documents_updated': 0,
                'message': f"Not enough documents for duplicate detection ({len(all_docs['documents']) if all_docs['documents'] else 0} found)"
            }
        
        print(f"🔍 Scanning {len(all_docs['documents'])} documents for duplicates...")
        
        # Generate embeddings for all documents
        doc_embeddings = []
        valid_docs = []
        
        for i, doc_content in enumerate(all_docs['documents']):
            try:
                # Skip documents that are too short
                if len(doc_content.strip()) < 50:
                    continue
                    
                embedding = embeddings.embed_query(doc_content)
                doc_embeddings.append(embedding)
                valid_docs.append(i)
            except Exception as e:
                print(f"Warning: Could not generate embedding for document {i}: {e}")
                continue
        
        if len(valid_docs) < 2:
            return {
                'success': True,
                'pairs_found': 0,
                'documents_updated': 0,
                'message': f"Not enough valid documents for duplicate detection ({len(valid_docs)} valid)"
            }
        
        # Calculate similarity matrix
        embedding_matrix = np.array(doc_embeddings)
        similarity_matrix = cosine_similarity(embedding_matrix)
        
        # Find similar document pairs above threshold
        similar_pairs = []
        similar_docs_metadata = {}
        
        for i in range(len(valid_docs)):
            for j in range(i + 1, len(valid_docs)):
                similarity_score = similarity_matrix[i][j]
                if similarity_score >= similarity_threshold:
                    doc_i_idx = valid_docs[i]
                    doc_j_idx = valid_docs[j]
                    
                    title_i = all_docs['metadatas'][doc_i_idx].get('title', f'Document {doc_i_idx+1}')
                    title_j = all_docs['metadatas'][doc_j_idx].get('title', f'Document {doc_j_idx+1}')
                    
                    similar_pairs.append((doc_i_idx, doc_j_idx, similarity_score))
                    print(f"  ✅ Found similar pair: '{title_i}' ↔ '{title_j}' (similarity: {similarity_score:.3f})")
                    
                    # Build similarity metadata
                    doc_i_id = all_docs['metadatas'][doc_i_idx].get('doc_id', f'doc_{doc_i_idx}')
                    doc_j_id = all_docs['metadatas'][doc_j_idx].get('doc_id', f'doc_{doc_j_idx}')
                    
                    if doc_i_id not in similar_docs_metadata:
                        similar_docs_metadata[doc_i_id] = []
                    if doc_j_id not in similar_docs_metadata:
                        similar_docs_metadata[doc_j_id] = []
                    
                    similar_docs_metadata[doc_i_id].append(doc_j_id)
                    similar_docs_metadata[doc_j_id].append(doc_i_id)
        
        # Update documents with new similarity relationships
        documents_to_update = []
        
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', f'doc_{i}')
            current_similar_docs = metadata.get('similar_docs', '')
            
            # Determine new similar_docs value
            if doc_id in similar_docs_metadata:
                new_similar_docs = ','.join(similar_docs_metadata[doc_id])
            else:
                new_similar_docs = ''
            
            # Update if different or if update_existing is True
            if update_existing or current_similar_docs != new_similar_docs:
                updated_metadata = metadata.copy()
                updated_metadata['similar_docs'] = new_similar_docs
                updated_metadata['doc_id'] = doc_id  # Ensure doc_id is set
                # Store timestamp with timezone info (EST/EDT)
                est = pytz.timezone('US/Eastern')
                current_time_est = datetime.now(est)
                updated_metadata['last_similarity_scan'] = current_time_est.isoformat()
                
                documents_to_update.append({
                    'id': all_docs['ids'][i],
                    'document': all_docs['documents'][i],
                    'metadata': updated_metadata
                })
        
        # Perform batch update if there are changes
        updated_count = 0
        if documents_to_update:
            try:
                # Delete existing documents
                ids_to_update = [item['id'] for item in documents_to_update]
                db.delete(ids_to_update)
                
                # Add them back with updated metadata
                db.add_documents(
                    documents=[Document(page_content=item['document'], metadata=item['metadata']) 
                             for item in documents_to_update],
                    ids=ids_to_update
                )
                updated_count = len(documents_to_update)
                print(f"✅ Updated {updated_count} documents with new similarity relationships")
                
            except Exception as e:
                print(f"Error updating documents: {e}")
                return {
                    'success': False,
                    'pairs_found': len(similar_pairs),
                    'documents_updated': 0,
                    'message': f"Found {len(similar_pairs)} pairs but failed to update documents: {str(e)}"
                }
        
        return {
            'success': True,
            'pairs_found': len(similar_pairs),
            'documents_updated': updated_count,
            'message': f"Successfully found {len(similar_pairs)} duplicate pairs and updated {updated_count} documents",
            'threshold_used': similarity_threshold
        }
        
    except Exception as e:
        print(f"Error during duplicate scan: {e}")
        return {
            'success': False,
            'pairs_found': 0,
            'documents_updated': 0,
            'message': f"Error during duplicate scan: {str(e)}"
        }


def cleanup_duplicate_database_entries():
    """Clean up duplicate entries in ChromaDB that have the same title"""
    try:
        if not db:
            return False, "ChromaDB not available"
        
        # Get all documents from the database
        all_docs = db.get()
        
        if not all_docs['ids']:
            return True, "No documents to clean up"
        
        # Group documents by title
        title_groups = {}
        for i, doc_id in enumerate(all_docs['ids']):
            metadata = all_docs['metadatas'][i]
            title = metadata.get('title', 'Unknown')
            
            if title not in title_groups:
                title_groups[title] = []
            title_groups[title].append({
                'id': doc_id,
                'metadata': metadata,
                'content': all_docs['documents'][i]
            })
        
        # Find and remove duplicates
        cleaned_count = 0
        for title, docs in title_groups.items():
            if len(docs) > 1:
                print(f"DEBUG: Found {len(docs)} documents with title '{title}'")
                
                # Keep the document that looks most like the original seeded data (doc_ prefix)
                # or the newest page_ document if no doc_ exists
                keep_doc = None
                remove_docs = []
                
                # Prefer doc_ prefixed IDs (original seeded data)
                doc_prefixed = [d for d in docs if d['id'].startswith('doc_')]
                if doc_prefixed:
                    keep_doc = doc_prefixed[0]  # Keep the first doc_ prefixed one
                    remove_docs = [d for d in docs if d != keep_doc]
                else:
                    # If no doc_ prefixed, keep the first one and remove others
                    keep_doc = docs[0]
                    remove_docs = docs[1:]
                
                # Remove duplicate documents
                for remove_doc in remove_docs:
                    try:
                        db.delete([remove_doc['id']])
                        print(f"DEBUG: Removed duplicate document '{remove_doc['id']}' with title '{title}'")
                        cleaned_count += 1
                    except Exception as e:
                        print(f"DEBUG: Error removing document '{remove_doc['id']}': {e}")
        
        return True, f"Cleaned up {cleaned_count} duplicate database entries"
        
    except Exception as e:
        return False, f"Error cleaning up duplicate entries: {str(e)}"


def extract_space_key_from_url(url):
    """Extract space key from Confluence URL"""
    if not url:
        return None
    
    try:
        # Method 1: /spaces/SPACEKEY/ format
        if '/spaces/' in url:
            parts = url.split('/spaces/')
            if len(parts) > 1:
                space_part = parts[1].split('/')[0]
                return space_part
        
        # Method 2: spaceKey parameter
        if 'spaceKey=' in url:
            space_key = url.split('spaceKey=')[1].split('&')[0]
            return space_key
        
        # Method 3: /display/SPACEKEY/ format
        if '/display/' in url:
            parts = url.split('/display/')
            if len(parts) > 1:
                space_part = parts[1].split('/')[0]
                return space_part
        
        return None
        
    except Exception as e:
        print(f"DEBUG: Error extracting space key from URL {url}: {e}")
        return None


def get_space_name_from_key(space_key):
    """Convert a space key to a space name using available spaces data"""
    if not space_key or space_key == 'Unknown':
        return 'Unknown Space'
    
    # Import here to avoid circular imports
    import streamlit as st
    
    # Get available spaces from session state
    available_spaces = st.session_state.get('available_spaces', [])
    
    if available_spaces:
        for space in available_spaces:
            if space['key'] == space_key:
                return space['name']
    
    # If space not found in available spaces, return the key as fallback
    return space_key


def get_detected_duplicates(space_filter=None, cross_space_only=False, within_space_only=False):
    """Get all document pairs that have been detected as duplicates, optionally filtered by spaces
    
    Args:
        space_filter (list): List of space keys to filter by. If None, returns all duplicates.
        cross_space_only (bool): If True, only return cross-space duplicates
        within_space_only (bool): If True, only return within-space duplicates
    """
    try:
        from langchain.schema import Document
        
        # Get all documents from the database
        all_docs = db.get()
        
        if not all_docs['documents']:
            return []
        
        duplicate_pairs = []
        processed_docs = set()
        
        # Create a mapping from doc_id to index for faster lookup
        doc_id_to_index = {}
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', '')
            if doc_id:
                doc_id_to_index[doc_id] = i
        
        # Process each document
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', '')
            
            if doc_id in processed_docs:
                continue
            
            content = all_docs['documents'][i]
            
            # Extract space key for filtering
            doc_space_key = extract_space_key_from_url(metadata.get('source', ''))
            
            # Apply space filter if provided
            if space_filter and doc_space_key not in space_filter:
                continue
            
            # Check if this document has similar documents
            similar_docs_str = metadata.get('similar_docs', '')
            if not similar_docs_str:
                continue
                
            similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
            
            # Find the similar documents
            for similar_doc_id in similar_doc_ids:
                if similar_doc_id in processed_docs:
                    continue
                    
                # Find the similar document using the doc_id mapping
                similar_doc_index = doc_id_to_index.get(similar_doc_id)
                
                if similar_doc_index is not None:
                    similar_metadata = all_docs['metadatas'][similar_doc_index]
                    
                    # Extract space key for the similar document
                    similar_space_key = extract_space_key_from_url(similar_metadata.get('source', ''))
                    
                    # Apply space filter for similar document if provided
                    if space_filter and similar_space_key not in space_filter:
                        continue
                    
                    # Apply cross-space filtering logic
                    if cross_space_only:
                        # Only include if documents are from different spaces
                        if doc_space_key == similar_space_key:
                            continue
                    elif within_space_only:
                        # Only include if documents are from the same space
                        if doc_space_key != similar_space_key:
                            continue
                    # If neither filter is set, include all duplicates
                    
                    # Create document objects
                    main_doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    
                    similar_doc = Document(
                        page_content=all_docs['documents'][similar_doc_index],
                        metadata=similar_metadata
                    )
                    
                    # Calculate similarity score using actual embeddings
                    try:
                        from sklearn.metrics.pairwise import cosine_similarity
                        import numpy as np
                        
                        # Generate embeddings for both documents
                        embedding1 = embeddings.embed_query(content)
                        embedding2 = embeddings.embed_query(all_docs['documents'][similar_doc_index])
                        
                        # Calculate cosine similarity
                        similarity_matrix = cosine_similarity([embedding1], [embedding2])
                        similarity_score = float(similarity_matrix[0][0])
                        
                    except Exception as e:
                        print(f"Warning: Could not calculate similarity for pair {doc_id}-{similar_doc_id}: {e}")
                        # Fall back to a reasonable default based on the fact they were detected as similar
                        similarity_score = 0.75  # Default similarity score
                    
                    duplicate_pairs.append({
                        'main_doc': main_doc,
                        'similar_doc': similar_doc,
                        'similarity_score': similarity_score,
                        'main_title': metadata.get('title', 'Untitled'),
                        'similar_title': similar_metadata.get('title', 'Untitled'),
                        'main_space': doc_space_key or 'Unknown',
                        'similar_space': similar_space_key or 'Unknown',
                        'main_space_name': get_space_name_from_key(doc_space_key),
                        'similar_space_name': get_space_name_from_key(similar_space_key)
                    })
                    
                    processed_docs.add(similar_doc_id)
            
            processed_docs.add(doc_id)
        
        return duplicate_pairs
    
    except Exception as e:
        import streamlit as st
        st.error(f"Error getting detected duplicates: {str(e)}")
        return []


def update_chroma_after_merge(main_doc, similar_doc, keep_main=True):
    """Update Chroma database after successful merge to remove duplicate relationships"""
    try:
        from utils.helpers import Document
        
        # Get the doc_id of the document we're keeping and the one we're removing
        main_doc_id = main_doc.metadata.get('doc_id', '')
        similar_doc_id = similar_doc.metadata.get('doc_id', '')
        
        if not main_doc_id or not similar_doc_id:
            print(f"DEBUG: Missing doc_ids for Chroma update. Main: {main_doc_id}, Similar: {similar_doc_id}")
            return False, "Missing document IDs for Chroma update"
        
        # Determine which document to keep and which to remove
        if keep_main:
            keep_doc_id = main_doc_id
            remove_doc_id = similar_doc_id
        else:
            keep_doc_id = similar_doc_id
            remove_doc_id = main_doc_id
        
        # Get all documents from Chroma
        all_docs = db.get()
        
        if not all_docs['documents']:
            return False, "No documents found in Chroma database"
        
        # Find and update documents that reference the removed document
        updated_count = 0
        documents_to_update = []
        
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', '')
            similar_docs_str = metadata.get('similar_docs', '')
            
            if similar_docs_str and remove_doc_id in similar_docs_str:
                # Remove the deleted document from similar_docs list
                similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
                similar_doc_ids = [id for id in similar_doc_ids if id != remove_doc_id]
                
                # Update the metadata
                updated_metadata = metadata.copy()
                updated_metadata['similar_docs'] = ','.join(similar_doc_ids) if similar_doc_ids else ''
                
                # Store the update information
                documents_to_update.append({
                    'id': all_docs['ids'][i],
                    'document': all_docs['documents'][i],
                    'metadata': updated_metadata
                })
                updated_count += 1
                print(f"DEBUG: Prepared update for document {doc_id} to remove reference to {remove_doc_id}")
        
        # Perform batch update using add (which overwrites existing documents with same IDs)
        if documents_to_update:
            try:
                # First delete the existing documents
                ids_to_update = [item['id'] for item in documents_to_update]
                db.delete(ids_to_update)
                
                # Then add them back with updated metadata
                db.add_documents(
                    documents=[Document(page_content=item['document'], metadata=item['metadata']) 
                             for item in documents_to_update],
                    ids=ids_to_update
                )
                print(f"DEBUG: Successfully updated {len(documents_to_update)} documents via delete+add")
            except Exception as e:
                print(f"DEBUG: Error during batch update: {e}")
                return False, f"Error updating documents: {str(e)}"
        
        # Remove the deleted document from Chroma entirely
        # Find the Chroma ID of the document to remove
        remove_chroma_id = None
        for i, metadata in enumerate(all_docs['metadatas']):
            if metadata.get('doc_id', '') == remove_doc_id:
                remove_chroma_id = all_docs['ids'][i]
                break
        
        if remove_chroma_id:
            db.delete([remove_chroma_id])
            print(f"DEBUG: Removed document {remove_doc_id} from Chroma database")
        
        return True, f"Updated {updated_count} documents and removed merged document from database"
        
    except Exception as e:
        print(f"DEBUG: Error updating Chroma after merge: {e}")
        return False, f"Error updating Chroma database: {str(e)}"
