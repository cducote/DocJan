"""
Test SharePoint API performance and connection
"""
import time
from sharepoint.api import SharePointAPI

def test_sharepoint_performance():
    """Test SharePoint API calls and measure performance"""
    print("🚀 Testing SharePoint API Performance...")
    print("=" * 50)
    
    # Test 1: Authentication
    start_time = time.time()
    try:
        sharepoint_api = SharePointAPI()
        auth_time = time.time() - start_time
        print(f"✅ Authentication: {auth_time:.2f}s")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Test 2: Get documents
    start_time = time.time()
    try:
        documents = sharepoint_api.get_documents("Concatly_Test_Documents")
        doc_time = time.time() - start_time
        print(f"✅ Get Documents: {doc_time:.2f}s ({len(documents)} docs)")
    except Exception as e:
        print(f"❌ Get documents failed: {e}")
        return
    
    # Test 3: Similarity calculations (simulated)
    start_time = time.time()
    pair_count = 0
    for i, doc1 in enumerate(documents):
        for j, doc2 in enumerate(documents[i+1:], i+1):
            # Simulate similarity calculation
            name1 = doc1['name'].lower()
            name2 = doc2['name'].lower()
            pair_count += 1
    
    calc_time = time.time() - start_time
    print(f"✅ Similarity Calculations: {calc_time:.2f}s ({pair_count} pairs)")
    
    # Total time
    total_time = auth_time + doc_time + calc_time
    print("=" * 50)
    print(f"🏁 Total estimated load time: {total_time:.2f}s")
    
    # Performance recommendations
    if total_time > 5:
        print("\n⚠️  Performance Issues Detected:")
        if auth_time > 2:
            print("   - Authentication is slow (>2s)")
        if doc_time > 2:
            print("   - Document loading is slow (>2s)")
        if calc_time > 1:
            print("   - Too many similarity calculations")
        print("\n💡 Recommendations:")
        print("   - Implement caching in session state")
        print("   - Reduce API calls")
        print("   - Add loading spinners")
    else:
        print("\n✅ Performance looks good!")

if __name__ == "__main__":
    test_sharepoint_performance()
