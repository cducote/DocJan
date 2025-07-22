#!/usr/bin/env python3
"""
Simple test script to verify merge tracking functionality
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import (
    store_merge_operation, 
    get_recent_merges, 
    undo_merge_operation,
    merge_collection,
    Document,
    restore_deleted_confluence_page,
    restore_confluence_page_version
)

def test_merge_tracking():
    """Test the merge tracking functionality"""
    print("🧪 Testing Merge Tracking Functionality")
    print("=" * 50)
    
    if not merge_collection:
        print("❌ ERROR: Merge collection not initialized")
        return False
    
    # Test 1: Store a merge operation
    print("\n1️⃣ Testing store_merge_operation...")
    try:
        success, message = store_merge_operation(
            kept_page_id="123456",
            deleted_page_id="789012",
            merged_content="<p>This is test merged content</p>",
            kept_title="Test Kept Page",
            deleted_title="Test Deleted Page",
            kept_url="https://example.com/kept",
            deleted_url="https://example.com/deleted"
        )
        
        if success:
            print(f"✅ Store operation successful: {message}")
        else:
            print(f"❌ Store operation failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Store operation error: {e}")
        return False
    
    # Test 2: Retrieve recent merges
    print("\n2️⃣ Testing get_recent_merges...")
    try:
        recent_merges = get_recent_merges(limit=5)
        print(f"✅ Found {len(recent_merges)} recent merges")
        
        if recent_merges:
            latest = recent_merges[0]
            print(f"   Latest merge: {latest['kept_title']} ← {latest['deleted_title']}")
            print(f"   Status: {latest['status']}")
            print(f"   Timestamp: {latest['timestamp']}")
        
    except Exception as e:
        print(f"❌ Get recent merges error: {e}")
        return False
    
    # Test 3: Test merge collection directly
    print("\n3️⃣ Testing ChromaDB merge collection...")
    try:
        all_merges = merge_collection.get()
        print(f"✅ Collection contains {len(all_merges['ids'])} merge records")
        
        if all_merges['ids']:
            print(f"   Sample record ID: {all_merges['ids'][0]}")
            print(f"   Sample metadata keys: {list(all_merges['metadatas'][0].keys())}")
        
    except Exception as e:
        print(f"❌ Collection access error: {e}")
        return False
    
    # Test 4: Clean up test data (optional)
    print("\n4️⃣ Cleaning up test data...")
    try:
        # Find and remove test records
        all_records = merge_collection.get()
        test_ids = []
        
        for i, metadata in enumerate(all_records['metadatas']):
            if (metadata.get('kept_title') == 'Test Kept Page' or 
                metadata.get('deleted_title') == 'Test Deleted Page'):
                test_ids.append(all_records['ids'][i])
        
        if test_ids:
            merge_collection.delete(test_ids)
            print(f"✅ Cleaned up {len(test_ids)} test records")
        else:
            print("✅ No test records found to clean up")
            
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False
    
    print("\n🎉 All tests passed! Merge tracking is working correctly.")
    return True

def test_chroma_connection():
    """Test basic ChromaDB connection"""
    print("\n🔍 Testing ChromaDB Connection")
    print("=" * 30)
    
    try:
        if merge_collection:
            # Test basic operations
            test_doc = Document(
                page_content="Test connection document",
                metadata={"test": True, "timestamp": datetime.now().isoformat()}
            )
            
            # Add test document
            test_id = f"test_conn_{int(datetime.now().timestamp())}"
            merge_collection.add_documents([test_doc], ids=[test_id])
            print("✅ Successfully added test document")
            
            # Retrieve test document
            result = merge_collection.get(ids=[test_id])
            if result['ids']:
                print("✅ Successfully retrieved test document")
            else:
                print("❌ Could not retrieve test document")
                return False
            
            # Delete test document
            merge_collection.delete([test_id])
            print("✅ Successfully deleted test document")
            
            return True
        else:
            print("❌ Merge collection not initialized")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB connection error: {e}")
        return False

def test_confluence_restore_methods():
    """Test the Confluence restore methods (for debugging)"""
    print("\n🔧 Testing Confluence Restore Methods (Debug Mode)")
    print("=" * 55)
    
    # Note: These are test functions that won't actually restore pages
    # unless you provide real page IDs
    
    print("1️⃣ Testing restore_deleted_confluence_page function structure...")
    try:
        # This will fail with "Page not found" but we can see the error handling
        success, message = restore_deleted_confluence_page("123456789")
        print(f"   Function executed: Success={success}")
        print(f"   Message: {message}")
        print("   ✅ Function structure is working")
    except Exception as e:
        print(f"   ❌ Function structure error: {e}")
        return False
    
    print("\n2️⃣ Testing restore_confluence_page_version function structure...")
    try:
        # This will fail but we can see the error handling
        success, message = restore_confluence_page_version("123456789", 1)
        print(f"   Function executed: Success={success}")
        print(f"   Message: {message}")
        print("   ✅ Function structure is working")
    except Exception as e:
        print(f"   ❌ Function structure error: {e}")
        return False
    
    print("\n✅ All restore function structures are working properly!")
    print("💡 To test with real pages, you would need:")
    print("   - A real page ID that exists in your Confluence trash")
    print("   - A real page ID with multiple versions for version restore")
    
    return True

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    print("🚀 Starting Merge Tracking Tests")
    print("=" * 40)
    
    # Test ChromaDB connection first
    if not test_chroma_connection():
        print("\n💥 ChromaDB connection test failed. Exiting.")
        sys.exit(1)
    
    # Test merge tracking functionality
    if not test_merge_tracking():
        print("\n💥 Merge tracking tests failed. Exiting.")
        sys.exit(1)
    
    # Test restore function structures
    if not test_confluence_restore_methods():
        print("\n💥 Restore function tests failed. Exiting.")
        sys.exit(1)
    
    print("\n🎊 All tests completed successfully!")
    print("\n📋 Summary:")
    print("✅ ChromaDB connection: Working")
    print("✅ Merge tracking: Working") 
    print("✅ Restore functions: Structure verified")
    print("\n💡 The system is ready for testing with real Confluence pages!")
    sys.exit(0)
