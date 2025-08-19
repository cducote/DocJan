"""
Vector Store Service - Core embedding and ChromaDB operations.
Extracted from Streamlit app for containerized deployment.
"""
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timezone


class VectorStoreService:
    """
    Core vector store operations service.
    Handles embedding generation, ChromaDB storage, and duplicate detection.
    Supports organization-based data isolation through collections.
    """
    
    def __init__(self, chroma_persist_dir: str = "./chroma_store", openai_api_key: Optional[str] = None, organization_id: Optional[str] = None):
        """
        Initialize vector store service.
        
        Args:
            chroma_persist_dir: Directory for ChromaDB persistence
            openai_api_key: OpenAI API key for embeddings (if None, uses environment)
            organization_id: Organization ID for data isolation (if None, uses default collection)
        """
        self.chroma_persist_dir = chroma_persist_dir
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.organization_id = organization_id
        
        # Generate collection name based on organization
        if organization_id:
            # Handle case where organization_id already has org_ prefix to avoid double prefixing
            if organization_id.startswith("org_"):
                self.collection_name = organization_id
                self.cache_collection_name = f"{organization_id}_cache"
            else:
                self.collection_name = f"org_{organization_id}"
                self.cache_collection_name = f"org_{organization_id}_cache"
        else:
            self.collection_name = "default"  # Fallback for legacy support
            self.cache_collection_name = "default_cache"
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        # Initialize components
        self._init_embeddings()
        self._init_database()
    
    def _init_embeddings(self):
        """Initialize OpenAI embeddings."""
        try:
            from langchain_openai import OpenAIEmbeddings
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=self.openai_api_key
            )
        except ImportError:
            raise ImportError("langchain_openai is required. Install with: pip install langchain-openai")
    
    def _init_database(self):
        """Initialize ChromaDB instance with organization-specific collection."""
        try:
            from langchain_chroma import Chroma
            import os
            
            # Ensure the persist directory exists
            if not os.path.exists(self.chroma_persist_dir):
                print(f"📁 [VECTOR_STORE] Creating ChromaDB directory: {self.chroma_persist_dir}")
                os.makedirs(self.chroma_persist_dir, exist_ok=True)
            
            # For production compatibility, disable tenant validation
            import chromadb
            settings = chromadb.config.Settings()
            settings.allow_reset = True
            
            self.db = Chroma(
                persist_directory=self.chroma_persist_dir,
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
                client_settings=settings
            )
            
            # Initialize separate cache collection for duplicate pairs
            self.cache_db = Chroma(
                persist_directory=self.chroma_persist_dir,
                embedding_function=self.embeddings,
                collection_name=self.cache_collection_name,
                client_settings=settings
            )
            
            print(f"🗄️ [VECTOR_STORE] Initialized ChromaDB with collection: {self.collection_name}")
            print(f"🗄️ [VECTOR_STORE] Initialized cache collection: {self.cache_collection_name}")
        except ImportError:
            raise ImportError("langchain_chroma is required. Install with: pip install langchain-chroma")
        except Exception as e:
            print(f"❌ [VECTOR_STORE] ChromaDB initialization failed, trying fallback: {e}")
            # Check if this is a settings conflict error
            if "different settings" in str(e).lower() or "settings" in str(e).lower():
                print(f"🔧 [VECTOR_STORE] Detected settings conflict, attempting to clear and reinitialize...")
                try:
                    self._clear_chroma_directory()
                    # Try again after clearing
                    from langchain_chroma import Chroma
                    import chromadb
                    settings = chromadb.config.Settings()
                    settings.allow_reset = True
                    
                    self.db = Chroma(
                        persist_directory=self.chroma_persist_dir,
                        embedding_function=self.embeddings,
                        collection_name=self.collection_name,
                        client_settings=settings
                    )
                    
                    # Initialize separate cache collection for duplicate pairs
                    self.cache_db = Chroma(
                        persist_directory=self.chroma_persist_dir,
                        embedding_function=self.embeddings,
                        collection_name=self.cache_collection_name,
                        client_settings=settings
                    )
                    
                    print(f"✅ [VECTOR_STORE] Successfully reinitialized after clearing: {self.collection_name}")
                    print(f"✅ [VECTOR_STORE] Successfully reinitialized cache collection: {self.cache_collection_name}")
                    return
                except Exception as clear_error:
                    print(f"⚠️ [VECTOR_STORE] Could not clear directory: {clear_error}")
            
            # Fallback: Use simpler client configuration
            try:
                from langchain_chroma import Chroma
                self.db = Chroma(
                    persist_directory=self.chroma_persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
                
                # Initialize separate cache collection for duplicate pairs
                self.cache_db = Chroma(
                    persist_directory=self.chroma_persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=self.cache_collection_name
                )
                
                print(f"🗄️ [VECTOR_STORE] Initialized ChromaDB with fallback config: {self.collection_name}")
                print(f"🗄️ [VECTOR_STORE] Initialized cache collection with fallback config: {self.cache_collection_name}")
            except Exception as fallback_error:
                print(f"💥 [VECTOR_STORE] Both ChromaDB configurations failed: {fallback_error}")
                print(f"⚠️ [VECTOR_STORE] Running in degraded mode - vector operations will be disabled")
                # Set databases to None so the app can still start
                self.db = None
                self.cache_db = None
    
    def _clear_chroma_directory(self):
        """
        Clear the ChromaDB directory to force a clean initialization.
        This helps resolve settings conflicts between different ChromaDB versions.
        """
        import shutil
        try:
            if os.path.exists(self.chroma_persist_dir):
                # Remove the entire directory
                shutil.rmtree(self.chroma_persist_dir)
                print(f"🗑️ [VECTOR_STORE] Cleared ChromaDB directory: {self.chroma_persist_dir}")
                
                # Recreate the directory
                os.makedirs(self.chroma_persist_dir, exist_ok=True)
                print(f"📁 [VECTOR_STORE] Recreated ChromaDB directory: {self.chroma_persist_dir}")
                
        except Exception as e:
            print(f"⚠️ [VECTOR_STORE] Could not clear ChromaDB directory: {e}")
            # Try alternative approach - clear just the chroma.sqlite3 file
            try:
                sqlite_file = os.path.join(self.chroma_persist_dir, "chroma.sqlite3")
                if os.path.exists(sqlite_file):
                    os.remove(sqlite_file)
                    print(f"🗑️ [VECTOR_STORE] Cleared ChromaDB sqlite file: {sqlite_file}")
            except Exception as sqlite_error:
                print(f"⚠️ [VECTOR_STORE] Could not clear ChromaDB sqlite file: {sqlite_error}")
                raise e
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test vector store connection and embedding generation.
        WARNING: This makes an OpenAI API call and should NOT be used in health checks!
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Test embedding generation
            test_text = "This is a test document for embedding generation."
            embedding = self.embeddings.embed_query(test_text)
            
            if not embedding or len(embedding) == 0:
                return False, "Embedding generation failed"
            
            # Test ChromaDB connection
            collection_count = len(self.db.get()['ids'])
            
            return True, f"Vector store connected successfully. Collection: {self.collection_name}, Documents: {collection_count}, Embedding dimension: {len(embedding)}"
            
        except Exception as e:
            return False, f"Vector store connection failed: {str(e)}"

    def test_connection_lightweight(self) -> Tuple[bool, str]:
        """
        Lightweight connection test that doesn't make expensive API calls.
        Safe for health checks and frequent monitoring.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # First check if we have the db attributes at all
            if not hasattr(self, 'db'):
                return False, "ChromaDB not initialized - db attribute missing"
            
            if not hasattr(self, 'cache_db'):
                return False, "ChromaDB cache not initialized - cache_db attribute missing"
                
            # Then check if they are None (degraded mode)
            if self.db is None:
                return False, "ChromaDB not initialized - running in degraded mode"
            
            if self.cache_db is None:
                return False, "ChromaDB cache not initialized - running in degraded mode"
            
            # Now it's safe to test basic ChromaDB connection
            try:
                # Safely get collection info
                db_result = self.db.get()
                if db_result and 'ids' in db_result:
                    collection_count = len(db_result['ids'])
                else:
                    collection_count = 0
            except Exception as db_error:
                # If we can't get the count, there's a real connection issue
                return False, f"ChromaDB collection error: {str(db_error)}"
                
            try:
                # Safely get cache info
                cache_result = self.cache_db.get()
                if cache_result and 'ids' in cache_result:
                    cache_count = len(cache_result['ids'])
                else:
                    cache_count = 0
            except Exception as cache_error:
                # Cache errors are less critical
                cache_count = 0
            
            return True, f"Vector store healthy. Collection: {self.collection_name} ({collection_count} docs), Cache: ({cache_count} items)"
            
        except Exception as e:
            # This should catch any other unexpected errors
            return False, f"Vector store connection test failed: {str(e)}"
    
    def add_documents(self, documents: List[Any], batch_size: int = 50) -> Tuple[bool, str]:
        """
        Add documents to the vector store with efficient batching.
        
        Args:
            documents: List of Document objects with page_content and metadata
            batch_size: Number of documents to process at once
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.db is None:
                return False, "ChromaDB not available - running in degraded mode"
            
            if not documents:
                return False, "No documents provided"
            
            total_docs = len(documents)
            added_count = 0
            
            # Process documents in batches for efficiency
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                
                # Generate document IDs for this batch
                doc_ids = []
                for doc in batch:
                    doc_id = doc.metadata.get('doc_id')
                    if not doc_id:
                        # Generate fallback ID
                        title = doc.metadata.get('title', 'untitled')
                        doc_id = f"doc_{hash(title + doc.page_content[:100]) % 1000000}"
                        doc.metadata['doc_id'] = doc_id
                    doc_ids.append(doc_id)
                
                # Add batch to ChromaDB (this will overwrite existing documents with same IDs)
                self.db.add_documents(batch, ids=doc_ids)
                added_count += len(batch)
                
                print(f"Added batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}: {len(batch)} documents")
            
            return True, f"Successfully added {added_count} documents to vector store"
            
        except Exception as e:
            return False, f"Error adding documents to vector store: {str(e)}"
    
    def get_document_count(self) -> int:
        """Get total number of documents in the vector store."""
        try:
            return len(self.db.get()['ids'])
        except Exception:
            return 0
    
    def get_duplicate_count(self) -> int:
        """
        Get count of duplicate pairs using cached data for speed.
        
        Returns:
            Number of duplicate pairs
        """
        try:
            # Try to get count from cached duplicate pairs first
            try:
                cached_pairs = self.db.get(where={"doc_type": "duplicate_pair"})
                if cached_pairs['documents']:
                    count = len(cached_pairs['documents'])
                    print(f"🚀 [DUPLICATE_COUNT] Found {count} cached duplicate pairs")
                    return count
            except Exception as e:
                print(f"⚠️ [DUPLICATE_COUNT] No cached pairs, falling back to metadata scan: {e}")
            
            # Fallback to original method
            all_docs = self.db.get()
            
            if not all_docs['documents']:
                return 0
            
            # Count unique pairs by looking at similar_docs metadata
            pairs_found = set()
            
            for metadata in all_docs['metadatas']:
                similar_docs_str = metadata.get('similar_docs', '')
                
                if not similar_docs_str:
                    continue
                
                doc_id = metadata.get('doc_id', '')
                similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
                
                for similar_id in similar_doc_ids:
                    # Create a unique pair identifier to avoid double counting
                    pair_key = tuple(sorted([doc_id, similar_id]))
                    pairs_found.add(pair_key)
            
            return len(pairs_found)
            
        except Exception as e:
            print(f"Error getting duplicate count: {e}")
            return 0
    
    def clear_all_documents(self) -> Tuple[bool, str]:
        """
        Clear all documents from the vector store and cache.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get all document IDs from main collection
            all_docs = self.db.get()
            docs_cleared = 0
            
            if all_docs['ids']:
                self.db.delete(all_docs['ids'])
                docs_cleared = len(all_docs['ids'])
            
            # Also clear the cache collection
            try:
                cache_docs = self.cache_db.get()
                cache_cleared = 0
                if cache_docs['ids']:
                    self.cache_db.delete(cache_docs['ids'])
                    cache_cleared = len(cache_docs['ids'])
                
                total_cleared = docs_cleared + cache_cleared
                if total_cleared > 0:
                    return True, f"Cleared {docs_cleared} documents and {cache_cleared} cached items from vector store"
                else:
                    return True, "Vector store was already empty"
            except Exception as cache_error:
                # If cache clearing fails, still report success for main collection
                print(f"Warning: Failed to clear cache collection: {cache_error}")
                if docs_cleared > 0:
                    return True, f"Cleared {docs_cleared} documents from vector store (cache clear failed)"
                else:
                    return True, "Vector store was already empty"
                    
        except Exception as e:
            return False, f"Error clearing vector store: {str(e)}"
    
    def scan_for_duplicates(self, similarity_threshold: float = 0.65, update_existing: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """
        Scan all documents for duplicates and update their similarity relationships.
        
        Args:
            similarity_threshold: Threshold for considering documents similar
            update_existing: Whether to update existing similarity relationships
            
        Returns:
            Tuple of (success, results_dict)
        """
        try:
            # Get all documents from ChromaDB
            all_docs = self.db.get()
            
            if not all_docs['documents'] or len(all_docs['documents']) < 2:
                return True, {
                    'pairs_found': 0,
                    'documents_updated': 0,
                    'message': f"Not enough documents for duplicate detection ({len(all_docs['documents']) if all_docs['documents'] else 0} found)",
                    'threshold_used': similarity_threshold
                }
            
            print(f"Scanning {len(all_docs['documents'])} documents for duplicates...")
            
            # Generate embeddings for all documents
            doc_embeddings = []
            valid_docs = []
            
            for i, doc_content in enumerate(all_docs['documents']):
                try:
                    # Skip documents that are too short
                    if len(doc_content.strip()) < 50:
                        continue
                        
                    embedding = self.embeddings.embed_query(doc_content)
                    doc_embeddings.append(embedding)
                    valid_docs.append(i)
                except Exception as e:
                    print(f"Warning: Could not generate embedding for document {i}: {e}")
                    continue
            
            if len(valid_docs) < 2:
                return True, {
                    'pairs_found': 0,
                    'documents_updated': 0,
                    'message': f"Not enough valid documents for duplicate detection ({len(valid_docs)} valid)",
                    'threshold_used': similarity_threshold
                }
            
            # Calculate similarity matrix
            from sklearn.metrics.pairwise import cosine_similarity
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
                        print(f"Found similar pair: '{title_i}' ↔ '{title_j}' (similarity: {similarity_score:.3f})")
                        
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
                    updated_metadata['doc_id'] = doc_id
                    updated_metadata['last_similarity_scan'] = datetime.now(timezone.utc).isoformat()
                    
                    documents_to_update.append({
                        'id': all_docs['ids'][i],
                        'document': all_docs['documents'][i],
                        'metadata': updated_metadata
                    })
            
            # Perform batch update if there are changes
            updated_count = 0
            if documents_to_update:
                try:
                    from langchain.schema import Document
                    
                    # Delete existing documents
                    ids_to_update = [item['id'] for item in documents_to_update]
                    self.db.delete(ids_to_update)
                    
                    # Add them back with updated metadata
                    self.db.add_documents(
                        documents=[Document(page_content=item['document'], metadata=item['metadata']) 
                                 for item in documents_to_update],
                        ids=ids_to_update
                    )
                    updated_count = len(documents_to_update)
                    print(f"Updated {updated_count} documents with new similarity relationships")
                    
                except Exception as e:
                    print(f"Error updating documents: {e}")
                    return False, {
                        'pairs_found': len(similar_pairs),
                        'documents_updated': 0,
                        'message': f"Found {len(similar_pairs)} pairs but failed to update documents: {str(e)}",
                        'threshold_used': similarity_threshold
                    }
            
            # Cache duplicate pairs for fast retrieval
            if similar_pairs:
                self._cache_duplicate_pairs(similar_pairs, all_docs)
            
            return True, {
                'pairs_found': len(similar_pairs),
                'documents_updated': updated_count,
                'message': f"Successfully found {len(similar_pairs)} duplicate pairs and updated {updated_count} documents",
                'threshold_used': similarity_threshold
            }
            
        except Exception as e:
            print(f"Error during duplicate scan: {e}")
            return False, {
                'pairs_found': 0,
                'documents_updated': 0,
                'message': f"Error during duplicate scan: {str(e)}",
                'threshold_used': similarity_threshold
            }
    
    def _cache_duplicate_pairs(self, similar_pairs, all_docs):
        """
        Cache duplicate pairs for fast retrieval.
        Stores each pair as a separate document with doc_type='duplicate_pair'.
        """
        try:
            # First, clear existing cached pairs
            try:
                existing_pairs = self.cache_db.get(where={"doc_type": "duplicate_pair"})
                if existing_pairs['ids']:
                    self.cache_db.delete(existing_pairs['ids'])
                    print(f"🗑️ [CACHE] Cleared {len(existing_pairs['ids'])} old cached pairs")
            except Exception as e:
                print(f"⚠️ [CACHE] Could not clear old pairs: {e}")
            
            # Cache new pairs
            from langchain.schema import Document
            cached_documents = []
            
            for i, (doc_i_idx, doc_j_idx, similarity_score) in enumerate(similar_pairs):
                metadata_i = all_docs['metadatas'][doc_i_idx]
                metadata_j = all_docs['metadatas'][doc_j_idx]
                
                # Create duplicate pair data structure
                pair_data = {
                    'id': i + 1,
                    'page1': {
                        'title': metadata_i.get('title', f'Document {doc_i_idx+1}'),
                        'url': metadata_i.get('source', ''),
                        'space': metadata_i.get('space_name', metadata_i.get('space_key', 'Unknown'))
                    },
                    'page2': {
                        'title': metadata_j.get('title', f'Document {doc_j_idx+1}'),
                        'url': metadata_j.get('source', ''),
                        'space': metadata_j.get('space_name', metadata_j.get('space_key', 'Unknown'))
                    },
                    'similarity': round(similarity_score, 3),
                    'status': 'pending'
                }
                
                # Store as a document with special metadata
                cached_documents.append(Document(
                    page_content=str(pair_data),  # Store the pair data as content
                    metadata={
                        'doc_type': 'duplicate_pair',
                        'pair_id': i + 1,
                        'similarity': similarity_score,
                        'cached_at': datetime.now(timezone.utc).isoformat()
                    }
                ))
            
            if cached_documents:
                self.cache_db.add_documents(cached_documents)
                print(f"💾 [CACHE] Cached {len(cached_documents)} duplicate pairs for fast retrieval")
                
        except Exception as e:
            print(f"❌ [CACHE] Error caching duplicate pairs: {e}")
    
    def get_duplicates(self) -> List[Dict[str, Any]]:
        """
        Get all detected duplicate pairs from the vector store.
        Fast implementation using cached duplicate pairs.
        Filters out resolved pairs so they don't appear in Content Report.
        
        Returns:
            List of duplicate pair dictionaries (only pending status)
        """
        try:
            # Try to get cached duplicate pairs first
            try:
                cached_pairs = self.cache_db.get(where={"doc_type": "duplicate_pair"})
                if cached_pairs['documents']:
                    all_pairs = [eval(doc) for doc in cached_pairs['documents']]
                    # Filter out resolved pairs
                    pending_pairs = [pair for pair in all_pairs if pair.get('status', 'pending') != 'resolved']
                    print(f"🚀 [DUPLICATES] Found {len(pending_pairs)} pending duplicate pairs (filtered out {len(all_pairs) - len(pending_pairs)} resolved)")
                    return pending_pairs
            except Exception as e:
                print(f"⚠️ [DUPLICATES] No cached pairs found, falling back to metadata scan: {e}")
            
            # Fallback to original method if no cached pairs
            all_docs = self.db.get()
            
            if not all_docs['documents']:
                return []
            
            duplicate_pairs = []
            processed_pairs = set()
            
            for i, metadata in enumerate(all_docs['metadatas']):
                # Skip duplicate pair documents
                if metadata.get('doc_type') == 'duplicate_pair':
                    continue
                    
                similar_docs_str = metadata.get('similar_docs', '')
                
                if not similar_docs_str:
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
                    
                    # Calculate similarity score using stored embeddings if available
                    try:
                        from sklearn.metrics.pairwise import cosine_similarity
                        
                        embedding1 = all_docs['embeddings'][i] if all_docs.get('embeddings') else None
                        embedding2 = all_docs['embeddings'][similar_idx] if all_docs.get('embeddings') else None
                        
                        if embedding1 and embedding2:
                            similarity_matrix = cosine_similarity([embedding1], [embedding2])
                            similarity = float(similarity_matrix[0][0])
                        else:
                            # Fallback to generating embeddings
                            embedding1 = self.embeddings.embed_query(all_docs['documents'][i])
                            embedding2 = self.embeddings.embed_query(all_docs['documents'][similar_idx])
                            similarity_matrix = cosine_similarity([embedding1], [embedding2])
                            similarity = float(similarity_matrix[0][0])
                        
                    except Exception as e:
                        print(f"Warning: Could not calculate similarity for pair {doc1_id}-{doc2_id}: {e}")
                        similarity = 0.75  # Default fallback
                    
                    duplicate_pairs.append({
                        "id": len(duplicate_pairs) + 1,
                        "page1": {
                            "title": metadata.get('title', 'Unknown'),
                            "url": metadata.get('source', ''),
                            "space": metadata.get('space_name', metadata.get('space_key', 'Unknown'))
                        },
                        "page2": {
                            "title": all_docs['metadatas'][similar_idx].get('title', 'Unknown'), 
                            "url": all_docs['metadatas'][similar_idx].get('source', ''),
                            "space": all_docs['metadatas'][similar_idx].get('space_name', 
                                   all_docs['metadatas'][similar_idx].get('space_key', 'Unknown'))
                        },
                        "similarity": round(similarity, 3),
                        "status": "pending"
                    })
            
            # Filter out resolved pairs by checking for resolved markers
            try:
                resolved_markers = self.db.get(where={"doc_type": "resolved_pair"})
                resolved_pair_ids = set()
                
                if resolved_markers.get('metadatas'):
                    for metadata in resolved_markers['metadatas']:
                        if metadata.get('pair_id'):
                            resolved_pair_ids.add(metadata['pair_id'])
                
                if resolved_pair_ids:
                    original_count = len(duplicate_pairs)
                    duplicate_pairs = [pair for pair in duplicate_pairs if pair['id'] not in resolved_pair_ids]
                    filtered_count = original_count - len(duplicate_pairs)
                    if filtered_count > 0:
                        print(f"🔍 [DUPLICATES] Filtered out {filtered_count} resolved pairs from fallback method")
                        
            except Exception as e:
                print(f"⚠️ [DUPLICATES] Could not check for resolved markers: {e}")
            
            return duplicate_pairs
            
        except Exception as e:
            print(f"Error getting duplicates: {e}")
            return []

    def get_duplicate_pairs(self) -> List[Dict[str, Any]]:
        """
        Get all detected duplicate pairs. Alias for get_duplicates for consistency.
        
        Returns:
            List of duplicate pair dictionaries
        """
        return self.get_duplicates()

    def mark_pair_as_resolved(self, pair_id: int) -> bool:
        """
        Mark a duplicate pair as resolved so it won't appear in future duplicate reports.
        Persists the resolved status to ChromaDB for permanent storage.
        
        Args:
            pair_id: ID of the duplicate pair to mark as resolved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, try to get cached duplicate pairs and update them
            try:
                cached_pairs = self.cache_db.get(where={"doc_type": "duplicate_pair"})
                if cached_pairs['documents']:
                    pairs_list = [eval(doc) for doc in cached_pairs['documents']]
                    
                    # Find and update the specific pair
                    pair_found = False
                    for pair in pairs_list:
                        if pair.get('id') == pair_id:
                            pair['status'] = 'resolved'
                            pair_found = True
                            print(f"✅ Found and updated pair {pair_id} to resolved status")
                            break
                    
                    if pair_found:
                        # Remove all cached duplicate pairs and re-add them with updated status
                        self.cache_db.delete(where={"doc_type": "duplicate_pair"})
                        print(f"🗑️ Removed old cached duplicate pairs")
                        
                        # Re-add updated pairs
                        for i, pair in enumerate(pairs_list):
                            self.cache_db.add(
                                documents=[str(pair)],
                                metadatas=[{"doc_type": "duplicate_pair", "pair_id": pair.get('id')}],
                                ids=[f"duplicate_pair_{pair.get('id', i)}"]
                            )
                        
                        print(f"💾 Persisted {len(pairs_list)} duplicate pairs with updated status")
                        return True
                    else:
                        print(f"⚠️ Duplicate pair {pair_id} not found in cached pairs")
                        
            except Exception as e:
                print(f"⚠️ Could not update cached pairs: {e}")
                
            # Fallback: Store a simple resolved marker for this pair
            try:
                self.db.add(
                    documents=[f"resolved_pair_{pair_id}"],
                    metadatas=[{"doc_type": "resolved_pair", "pair_id": pair_id}],
                    ids=[f"resolved_pair_{pair_id}"]
                )
                print(f"✅ Stored resolved marker for pair {pair_id}")
                return True
                
            except Exception as e:
                print(f"❌ Failed to store resolved marker: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Error marking pair {pair_id} as resolved: {e}")
            return False

    def get_document_by_metadata(self, page_metadata: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Get full document content by matching metadata (title, URL, etc.).
        
        Args:
            page_metadata: Dictionary containing title, url, and other metadata to match
            
        Returns:
            Dictionary with content and metadata, or None if not found
        """
        try:
            all_docs = self.db.get()
            
            if not all_docs['documents']:
                return None
            
            target_title = page_metadata.get('title', '').strip()
            target_url = page_metadata.get('url', '').strip()
            
            # Try to find by exact title and URL match first
            for i, metadata in enumerate(all_docs['metadatas']):
                doc_title = metadata.get('title', '').strip()
                doc_url = metadata.get('source', '').strip()
                
                if doc_title == target_title and doc_url == target_url:
                    return {
                        'content': all_docs['documents'][i],
                        'metadata': metadata
                    }
            
            # Fallback: try to find by title only
            for i, metadata in enumerate(all_docs['metadatas']):
                doc_title = metadata.get('title', '').strip()
                
                if doc_title == target_title:
                    return {
                        'content': all_docs['documents'][i],
                        'metadata': metadata
                    }
            
            print(f"⚠️ [DOCUMENT LOOKUP] Could not find document with title: {target_title}")
            return None
            
        except Exception as e:
            print(f"❌ [DOCUMENT LOOKUP] Error retrieving document: {e}")
            return None


class VectorStoreConfig:
    """Configuration helper for vector store service."""
    
    @staticmethod
    def from_environment() -> Tuple[str, str]:
        """
        Load vector store configuration from environment variables.
        
        Returns:
            Tuple of (chroma_persist_dir, openai_api_key)
        """
        # Use centralized configuration
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent))
            from config.environment import config
            
            chroma_persist_dir = config.chroma_persist_directory
            openai_api_key = config.openai_api_key
            
            return chroma_persist_dir, openai_api_key
        except ImportError:
            # Fallback to direct environment variables if config module not available
            chroma_persist_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')
            openai_api_key = os.getenv('OPENAI_API_KEY')
            
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            return chroma_persist_dir, openai_api_key
    
    @staticmethod
    def create_service_from_env(organization_id: Optional[str] = None) -> VectorStoreService:
        """
        Create a VectorStoreService instance from environment variables.
        
        Args:
            organization_id: Organization ID for data isolation (optional)
        
        Returns:
            Configured VectorStoreService instance
        """
        chroma_persist_dir, openai_api_key = VectorStoreConfig.from_environment()
        return VectorStoreService(chroma_persist_dir, openai_api_key, organization_id)
