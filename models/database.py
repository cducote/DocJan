"""
Database operations and management for DocJanitor.
"""
import os
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
        
        return merge_record
    
    except Exception as e:
        print(f"Error storing merge operation: {str(e)}")
        return None


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
