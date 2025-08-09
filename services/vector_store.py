"""
Vector Store Service - Handles embedding generation and ChromaDB operations.
Extracted from the original Streamlit app for containerization.
"""
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import pytz
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class DuplicatePair:
    """Represents a pair of similar documents."""
    doc1_id: str
    doc2_id: str
    doc1_title: str
    doc2_title: str
    doc1_url: str
    doc2_url: str
    doc1_space: str
    doc2_space: str
    similarity: float


@dataclass
class DuplicateResults:
    """Results of duplicate detection."""
    success: bool
    message: str
    pairs: List[DuplicatePair] = None
    total_documents: int = 0
    documents_with_duplicates: int = 0


class VectorStoreService:
    """
    Service for managing vector embeddings and duplicate detection.
    Wraps ChromaDB operations and similarity analysis.
    """
    
    def __init__(self, chroma_db, embeddings_model):
        """
        Initialize with ChromaDB instance and embeddings model.
        
        Args:
            chroma_db: ChromaDB instance
            embeddings_model: Embeddings model (e.g., OpenAIEmbeddings)
        """
        self.db = chroma_db
        self.embeddings = embeddings_model
    
    def add_documents(self, documents: List[Any], ids: List[str]) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects with content and metadata
            ids: List of document IDs
        
        Returns:
            Success status
        """
        try:
            self.db.add_documents(documents, ids=ids)
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def get_all_documents(self) -> Dict[str, Any]:
        """
        Get all documents from the vector store.
        
        Returns:
            Dictionary with documents, metadatas, ids, and embeddings
        """
        try:
            return self.db.get()
        except Exception as e:
            logger.error(f"Error retrieving documents from vector store: {e}")
            return {'documents': [], 'metadatas': [], 'ids': [], 'embeddings': []}
    
    def get_document_count(self) -> int:
        """Get total number of documents in the vector store."""
        try:
            all_docs = self.get_all_documents()
            return len(all_docs.get('documents', []))
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    def detect_duplicates(self, similarity_threshold: float = 0.75) -> DuplicateResults:
        """
        Detect duplicate documents using semantic similarity.
        
        Args:
            similarity_threshold: Minimum similarity score to consider documents duplicates
        
        Returns:
            DuplicateResults with found duplicate pairs
        """
        try:
            # Get all documents from vector store
            all_docs = self.get_all_documents()
            
            if not all_docs['documents'] or len(all_docs['documents']) < 2:
                return DuplicateResults(
                    success=True,
                    message=f"Not enough documents for duplicate detection ({len(all_docs['documents']) if all_docs['documents'] else 0} found)",
                    pairs=[],
                    total_documents=len(all_docs['documents']) if all_docs['documents'] else 0
                )
            
            logger.info(f"🔍 Scanning {len(all_docs['documents'])} documents for duplicates...")
            
            # Check if we have stored embeddings, otherwise generate them
            if all_docs.get('embeddings') and len(all_docs['embeddings']) == len(all_docs['documents']):
                # Use stored embeddings
                doc_embeddings = all_docs['embeddings']
                valid_docs = list(range(len(all_docs['documents'])))
                logger.info("Using stored embeddings for similarity calculation")
            else:
                # Generate embeddings for documents
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
                        logger.warning(f"Could not generate embedding for document {i}: {e}")
                        continue
                
                logger.info(f"Generated embeddings for {len(valid_docs)} valid documents")
            
            if len(valid_docs) < 2:
                return DuplicateResults(
                    success=True,
                    message=f"Not enough valid documents for duplicate detection ({len(valid_docs)} valid)",
                    pairs=[],
                    total_documents=len(all_docs['documents'])
                )
            
            # Calculate similarity matrix
            embedding_matrix = np.array(doc_embeddings)
            similarity_matrix = cosine_similarity(embedding_matrix)
            
            # Find similar document pairs above threshold
            duplicate_pairs = []
            unique_docs_with_duplicates = set()
            
            for i in range(len(valid_docs)):
                for j in range(i + 1, len(valid_docs)):
                    similarity_score = similarity_matrix[i][j]
                    
                    if similarity_score >= similarity_threshold:
                        doc_i_idx = valid_docs[i]
                        doc_j_idx = valid_docs[j]
                        
                        metadata_i = all_docs['metadatas'][doc_i_idx]
                        metadata_j = all_docs['metadatas'][doc_j_idx]
                        
                        title_i = metadata_i.get('title', f'Document {doc_i_idx+1}')
                        title_j = metadata_j.get('title', f'Document {doc_j_idx+1}')
                        
                        # Create duplicate pair
                        pair = DuplicatePair(
                            doc1_id=metadata_i.get('doc_id', f'doc_{doc_i_idx}'),
                            doc2_id=metadata_j.get('doc_id', f'doc_{doc_j_idx}'),
                            doc1_title=title_i,
                            doc2_title=title_j,
                            doc1_url=metadata_i.get('source', ''),
                            doc2_url=metadata_j.get('source', ''),
                            doc1_space=metadata_i.get('space_name', metadata_i.get('space_key', 'Unknown')),
                            doc2_space=metadata_j.get('space_name', metadata_j.get('space_key', 'Unknown')),
                            similarity=round(similarity_score, 3)
                        )
                        
                        duplicate_pairs.append(pair)
                        unique_docs_with_duplicates.add(pair.doc1_id)
                        unique_docs_with_duplicates.add(pair.doc2_id)
                        
                        logger.info(f"  ✅ Found duplicate: '{title_i}' ↔ '{title_j}' (similarity: {similarity_score:.3f})")
            
            return DuplicateResults(
                success=True,
                message=f"Found {len(duplicate_pairs)} duplicate pairs among {len(all_docs['documents'])} documents",
                pairs=duplicate_pairs,
                total_documents=len(all_docs['documents']),
                documents_with_duplicates=len(unique_docs_with_duplicates)
            )
            
        except Exception as e:
            logger.error(f"Error during duplicate detection: {e}")
            return DuplicateResults(
                success=False,
                message=f"Error during duplicate detection: {str(e)}",
                pairs=[]
            )
    
    def update_similarity_relationships(self, similarity_threshold: float = 0.75) -> Tuple[bool, str, int]:
        """
        Update document metadata with similarity relationships.
        
        Args:
            similarity_threshold: Minimum similarity score to consider documents similar
        
        Returns:
            Tuple of (success, message, documents_updated)
        """
        try:
            # Get duplicate detection results
            results = self.detect_duplicates(similarity_threshold)
            
            if not results.success:
                return False, results.message, 0
            
            # Build similarity mapping
            similarity_map = {}
            for pair in results.pairs:
                if pair.doc1_id not in similarity_map:
                    similarity_map[pair.doc1_id] = []
                if pair.doc2_id not in similarity_map:
                    similarity_map[pair.doc2_id] = []
                
                similarity_map[pair.doc1_id].append(pair.doc2_id)
                similarity_map[pair.doc2_id].append(pair.doc1_id)
            
            # Get all documents
            all_docs = self.get_all_documents()
            documents_to_update = []
            
            # Update metadata with similarity relationships
            for i, metadata in enumerate(all_docs['metadatas']):
                doc_id = metadata.get('doc_id', f'doc_{i}')
                
                # Update similar_docs metadata
                if doc_id in similarity_map:
                    new_similar_docs = ','.join(similarity_map[doc_id])
                else:
                    new_similar_docs = ''
                
                updated_metadata = metadata.copy()
                updated_metadata['similar_docs'] = new_similar_docs
                updated_metadata['doc_id'] = doc_id
                
                # Add timestamp
                est = pytz.timezone('US/Eastern')
                current_time_est = datetime.now(est)
                updated_metadata['last_similarity_scan'] = current_time_est.isoformat()
                
                documents_to_update.append({
                    'id': all_docs['ids'][i],
                    'document': all_docs['documents'][i],
                    'metadata': updated_metadata
                })
            
            # Perform batch update
            if documents_to_update:
                # Import Document class for update
                from langchain_core.documents import Document
                
                # Delete existing documents
                ids_to_update = [item['id'] for item in documents_to_update]
                self.db.delete(ids_to_update)
                
                # Add them back with updated metadata
                self.db.add_documents(
                    documents=[Document(page_content=item['document'], metadata=item['metadata']) 
                             for item in documents_to_update],
                    ids=ids_to_update
                )
                
                logger.info(f"✅ Updated {len(documents_to_update)} documents with similarity relationships")
                return True, f"Updated {len(documents_to_update)} documents with similarity relationships", len(documents_to_update)
            else:
                return True, "No documents to update", 0
                
        except Exception as e:
            logger.error(f"Error updating similarity relationships: {e}")
            return False, f"Error updating similarity relationships: {str(e)}", 0
    
    def clear_all_documents(self) -> bool:
        """
        Clear all documents from the vector store.
        
        Returns:
            Success status
        """
        try:
            # Get all document IDs
            all_docs = self.get_all_documents()
            if all_docs['ids']:
                self.db.delete(all_docs['ids'])
                logger.info(f"Cleared {len(all_docs['ids'])} documents from vector store")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for the vector store.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            all_docs = self.get_all_documents()
            
            # Calculate basic stats
            total_docs = len(all_docs.get('documents', []))
            
            # Count documents by space
            space_counts = {}
            docs_with_duplicates = 0
            
            for metadata in all_docs.get('metadatas', []):
                space_key = metadata.get('space_key', 'Unknown')
                space_counts[space_key] = space_counts.get(space_key, 0) + 1
                
                if metadata.get('similar_docs'):
                    docs_with_duplicates += 1
            
            return {
                'total_documents': total_docs,
                'documents_with_duplicates': docs_with_duplicates,
                'spaces': space_counts,
                'has_embeddings': bool(all_docs.get('embeddings'))
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                'total_documents': 0,
                'documents_with_duplicates': 0,
                'spaces': {},
                'has_embeddings': False
            }
