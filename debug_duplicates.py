# debug_duplicates.py - Script to debug the duplicate detection issue

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_store")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

def debug_database():
    """Debug the current state of the Chroma database"""
    print("[DEBUG] Analyzing Chroma database...")
    
    # Get all documents
    all_docs = db.get()
    
    if not all_docs['documents']:
        print("[ERROR] No documents found in database!")
        return
    
    print(f"[INFO] Total documents in database: {len(all_docs['documents'])}")
    print(f"[INFO] Total metadata entries: {len(all_docs['metadatas'])}")
    print("-" * 60)
    
    # Analyze each document
    doc_id_counts = {}
    title_counts = {}
    
    for i, metadata in enumerate(all_docs['metadatas']):
        doc_id = metadata.get('doc_id', 'NO_ID')
        title = metadata.get('title', 'NO_TITLE')
        similar_docs = metadata.get('similar_docs', '')
        
        # Count occurrences
        doc_id_counts[doc_id] = doc_id_counts.get(doc_id, 0) + 1
        title_counts[title] = title_counts.get(title, 0) + 1
        
        print(f"[{i+1}] ID: {doc_id}")
        print(f"     Title: {title}")
        print(f"     Similar: {similar_docs}")
        print(f"     Content preview: {all_docs['documents'][i][:50]}...")
        print()
    
    print("-" * 60)
    print("[ANALYSIS] Document ID counts:")
    for doc_id, count in doc_id_counts.items():
        if count > 1:
            print(f"[WARNING] '{doc_id}' appears {count} times!")
        else:
            print(f"[OK] '{doc_id}' appears {count} time")
    
    print("\n[ANALYSIS] Title counts:")
    for title, count in title_counts.items():
        if count > 1:
            print(f"[WARNING] '{title}' appears {count} times!")
        else:
            print(f"[OK] '{title}' appears {count} time")
    
    # Check for orphaned references
    print("\n[ANALYSIS] Checking for orphaned similar_docs references...")
    all_doc_ids = set(metadata.get('doc_id', '') for metadata in all_docs['metadatas'])
    
    for i, metadata in enumerate(all_docs['metadatas']):
        similar_docs_str = metadata.get('similar_docs', '')
        if similar_docs_str:
            similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
            for similar_id in similar_doc_ids:
                if similar_id not in all_doc_ids:
                    title = metadata.get('title', 'NO_TITLE')
                    print(f"[ERROR] '{title}' references non-existent doc_id: '{similar_id}'")

if __name__ == "__main__":
    debug_database()
