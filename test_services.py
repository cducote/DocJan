#!/usr/bin/env python3
"""
Simple test script to verify the services work before running the full FastAPI app.
"""
import os
import sys
sys.path.append('/Users/chrissyd/DocJan')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/Users/chrissyd/DocJan/services/.env')

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        from services.confluence_service import ConfluenceService
        print("✅ ConfluenceService imported successfully")
    except ImportError as e:
        print(f"❌ ConfluenceService import failed: {e}")
        return False
    
    try:
        from services.vector_store_service import VectorStoreService
        print("✅ VectorStoreService imported successfully")
    except ImportError as e:
        print(f"❌ VectorStoreService import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables."""
    print("\nTesting environment...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OPENAI_API_KEY found (ends with: ...{openai_key[-10:]})")
    else:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    chroma_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')
    print(f"✅ CHROMA_PERSIST_DIRECTORY: {chroma_dir}")
    
    return True

def test_confluence_service():
    """Test Confluence service creation."""
    print("\nTesting Confluence service...")
    
    try:
        from services.confluence_service import ConfluenceService
        
        # Test with dummy credentials
        confluence = ConfluenceService(
            base_url="https://test.atlassian.net/wiki",
            username="test@test.com",
            api_token="dummy_token"
        )
        print("✅ ConfluenceService created successfully")
        return True
    except Exception as e:
        print(f"❌ ConfluenceService creation failed: {e}")
        return False

def test_vector_store_service():
    """Test vector store service creation."""
    print("\nTesting Vector store service...")
    
    try:
        from services.vector_store_service import VectorStoreService
        
        openai_key = os.getenv('OPENAI_API_KEY')
        chroma_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')
        
        vector_store = VectorStoreService(
            chroma_persist_dir=chroma_dir,
            openai_api_key=openai_key
        )
        print("✅ VectorStoreService created successfully")
        return True
    except Exception as e:
        print(f"❌ VectorStoreService creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running service tests...\n")
    
    success = True
    success &= test_imports()
    success &= test_environment()
    success &= test_confluence_service()
    success &= test_vector_store_service()
    
    if success:
        print("\n🎉 All tests passed! Ready to run the FastAPI service.")
        print("\nTo start the service, run:")
        print("cd /Users/chrissyd/DocJan && /opt/homebrew/bin/python3.12 services/main.py")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
