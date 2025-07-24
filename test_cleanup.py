#!/usr/bin/env python3
"""Test script to run database cleanup"""

import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

# Initialize ChromaDB
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_store")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

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

if __name__ == "__main__":
    print("Running database cleanup...")
    success, message = cleanup_duplicate_database_entries()
    print(f"Result: {message}")
    
    # Show state after cleanup
    print("\nDatabase state after cleanup:")
    all_docs = db.get()
    print(f"Total documents: {len(all_docs['ids'])}")
    
    title_counts = {}
    for i, doc_id in enumerate(all_docs['ids']):
        title = all_docs['metadatas'][i].get('title', 'Unknown')
        title_counts[title] = title_counts.get(title, 0) + 1
    
    for title, count in title_counts.items():
        if count > 1:
            print(f"DUPLICATE: '{title}' appears {count} times")
        else:
            print(f"OK: '{title}' appears {count} time")
