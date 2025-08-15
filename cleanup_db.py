#!/usr/bin/env python3
"""
Safe ChromaDB cleanup script.
Shows you what's in your database and allows selective deletion.
"""

import os
import sys
import chromadb
from config.environment import get_chroma_persist_directory

def get_client():
    """Get ChromaDB client."""
    persist_dir = get_chroma_persist_directory()
    print(f"📁 ChromaDB directory: {persist_dir}")
    
    if not os.path.exists(persist_dir):
        print(f"❌ ChromaDB directory does not exist: {persist_dir}")
        return None
    
    client = chromadb.PersistentClient(path=persist_dir)
    return client

def list_collections():
    """List all collections in the database."""
    client = get_client()
    if not client:
        return []
    
    try:
        collections = client.list_collections()
        print(f"\n📊 Found {len(collections)} collections:")
        
        for i, collection in enumerate(collections, 1):
            doc_count = collection.count()
            print(f"  {i}. {collection.name} ({doc_count} documents)")
            
        return collections
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        return []

def show_collection_details(collection_name: str):
    """Show details about a specific collection."""
    client = get_client()
    if not client:
        return
    
    try:
        collection = client.get_collection(collection_name)
        doc_count = collection.count()
        
        print(f"\n📋 Collection: {collection_name}")
        print(f"📊 Document count: {doc_count}")
        
        if doc_count > 0:
            # Get a sample of documents
            sample = collection.get(limit=5)
            if sample['metadatas']:
                print(f"\n📄 Sample metadata:")
                for i, metadata in enumerate(sample['metadatas'][:3], 1):
                    print(f"  {i}. {metadata}")
                    
    except Exception as e:
        print(f"❌ Error getting collection details: {e}")

def delete_collection(collection_name: str):
    """Delete a specific collection."""
    client = get_client()
    if not client:
        return False
    
    try:
        # Confirm deletion
        response = input(f"\n⚠️  Are you sure you want to delete collection '{collection_name}'? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Deletion cancelled.")
            return False
        
        client.delete_collection(collection_name)
        print(f"✅ Deleted collection: {collection_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting collection: {e}")
        return False

def delete_entire_database():
    """Delete the entire ChromaDB directory."""
    persist_dir = get_chroma_persist_directory()
    
    print(f"\n⚠️  WARNING: This will delete the entire ChromaDB directory:")
    print(f"📁 {persist_dir}")
    
    response = input("\nType 'DELETE_EVERYTHING' to confirm: ")
    if response != 'DELETE_EVERYTHING':
        print("❌ Deletion cancelled.")
        return False
    
    try:
        import shutil
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
            print(f"✅ Deleted entire ChromaDB directory: {persist_dir}")
            return True
        else:
            print(f"❌ Directory does not exist: {persist_dir}")
            return False
    except Exception as e:
        print(f"❌ Error deleting directory: {e}")
        return False

def main():
    print("🗄️  ChromaDB Cleanup Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. List all collections")
        print("2. Show collection details")
        print("3. Delete specific collection")
        print("4. Delete entire database")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            list_collections()
            
        elif choice == '2':
            collections = list_collections()
            if collections:
                try:
                    index = int(input("\nEnter collection number: ")) - 1
                    if 0 <= index < len(collections):
                        show_collection_details(collections[index].name)
                    else:
                        print("❌ Invalid collection number.")
                except ValueError:
                    print("❌ Please enter a valid number.")
                    
        elif choice == '3':
            collections = list_collections()
            if collections:
                try:
                    index = int(input("\nEnter collection number to delete: ")) - 1
                    if 0 <= index < len(collections):
                        delete_collection(collections[index].name)
                    else:
                        print("❌ Invalid collection number.")
                except ValueError:
                    print("❌ Please enter a valid number.")
                    
        elif choice == '4':
            delete_entire_database()
            
        elif choice == '5':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
