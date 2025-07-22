#!/usr/bin/env python3
"""
Test script for automatic duplicate detection functionality.

This script tests the new scan_for_duplicates() function that can be called
after undo operations or manually triggered from the UI.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import the scan function from app.py
try:
    from app import scan_for_duplicates, db, get_detected_duplicates
    print("✅ Successfully imported duplicate detection functions")
except ImportError as e:
    print(f"❌ Failed to import functions: {e}")
    sys.exit(1)

def test_duplicate_scan():
    """Test the automatic duplicate detection scan"""
    print("\n🔍 Testing Automatic Duplicate Detection")
    print("=" * 50)
    
    # Test 1: Check current state
    print("\n1. Checking current database state...")
    try:
        all_docs = db.get()
        doc_count = len(all_docs['documents']) if all_docs['documents'] else 0
        print(f"   📊 Total documents in ChromaDB: {doc_count}")
        
        if doc_count < 2:
            print("   ⚠️  Warning: Need at least 2 documents for duplicate detection")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        return False
    
    # Test 2: Check current detected duplicates
    print("\n2. Checking currently detected duplicates...")
    try:
        current_duplicates = get_detected_duplicates()
        print(f"   📋 Current duplicate pairs: {len(current_duplicates)}")
        
        for i, pair in enumerate(current_duplicates, 1):
            print(f"      {i}. '{pair['main_title']}' ↔ '{pair['similar_title']}' (score: {pair['similarity_score']:.3f})")
            
    except Exception as e:
        print(f"   ❌ Error getting current duplicates: {e}")
        return False
    
    # Test 3: Run duplicate scan
    print("\n3. Running automatic duplicate scan...")
    try:
        scan_result = scan_for_duplicates(similarity_threshold=0.65, update_existing=True)
        
        if scan_result['success']:
            print(f"   ✅ Scan successful!")
            print(f"   📊 Pairs found: {scan_result['pairs_found']}")
            print(f"   🔄 Documents updated: {scan_result['documents_updated']}")
            print(f"   🎯 Threshold used: {scan_result['threshold_used']}")
            print(f"   💬 Message: {scan_result['message']}")
        else:
            print(f"   ❌ Scan failed: {scan_result['message']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during scan: {e}")
        return False
    
    # Test 4: Check duplicates after scan
    print("\n4. Checking duplicates after scan...")
    try:
        new_duplicates = get_detected_duplicates()
        print(f"   📋 Duplicate pairs after scan: {len(new_duplicates)}")
        
        for i, pair in enumerate(new_duplicates, 1):
            print(f"      {i}. '{pair['main_title']}' ↔ '{pair['similar_title']}' (score: {pair['similarity_score']:.3f})")
            
        if len(new_duplicates) != len(current_duplicates):
            print(f"   🔄 Duplicate count changed from {len(current_duplicates)} to {len(new_duplicates)}")
        else:
            print(f"   📊 Duplicate count remained the same: {len(new_duplicates)}")
            
    except Exception as e:
        print(f"   ❌ Error getting duplicates after scan: {e}")
        return False
    
    # Test 5: Test with different thresholds
    print("\n5. Testing different similarity thresholds...")
    thresholds = [0.50, 0.60, 0.70, 0.80]
    
    for threshold in thresholds:
        try:
            result = scan_for_duplicates(similarity_threshold=threshold, update_existing=False)
            if result['success']:
                print(f"   📊 Threshold {threshold}: {result['pairs_found']} pairs found")
            else:
                print(f"   ❌ Threshold {threshold}: Error - {result['message']}")
        except Exception as e:
            print(f"   ❌ Error testing threshold {threshold}: {e}")
    
    print("\n✅ Duplicate detection test completed!")
    return True

def test_metadata_inspection():
    """Inspect document metadata to understand similarity relationships"""
    print("\n🔬 Inspecting Document Metadata")
    print("=" * 50)
    
    try:
        all_docs = db.get()
        
        if not all_docs['documents']:
            print("   ❌ No documents found in database")
            return False
        
        print(f"\n📊 Found {len(all_docs['documents'])} documents")
        
        docs_with_similar = 0
        total_relationships = 0
        
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', f'doc_{i}')
            title = metadata.get('title', 'Untitled')
            similar_docs = metadata.get('similar_docs', '')
            last_scan = metadata.get('last_similarity_scan', 'Never')
            
            if similar_docs:
                docs_with_similar += 1
                similar_list = [s.strip() for s in similar_docs.split(',') if s.strip()]
                total_relationships += len(similar_list)
                
                print(f"\n   📄 Document {i+1}: {title}")
                print(f"      🆔 Doc ID: {doc_id}")
                print(f"      🔗 Similar to: {len(similar_list)} docs ({', '.join(similar_list)})")
                print(f"      🕐 Last scan: {last_scan}")
            else:
                print(f"\n   📄 Document {i+1}: {title} (no similarities)")
        
        print(f"\n📈 Summary:")
        print(f"   - Documents with similarities: {docs_with_similar}/{len(all_docs['documents'])}")
        print(f"   - Total similarity relationships: {total_relationships}")
        print(f"   - Expected duplicate pairs: {total_relationships // 2}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting metadata: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Duplicate Detection Test Suite")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_duplicate_scan()
    test2_passed = test_metadata_inspection()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Duplicate Scan Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Metadata Inspection: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Automatic duplicate detection is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)
