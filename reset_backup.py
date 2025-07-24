import os
import requests
import json
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import shutil
import subprocess
import sys

# Load environment variables
load_dotenv()

# Confluence API configuration
CONFLUENCE_USERNAME = os.getenv("CONFLUE    print(f"\n📊 Final Results:")
    print(f"   🌐 Spaces processed: {', '.join(space_keys)}")
    print(f"   📝 Confluence pages deleted: {len(all_deleted_pages)}")
    print(f"   📝 Confluence deletion failures: {len(all_failed_deletions)}")
    print(f"   🗃️  Chroma database reset: {'✅ Success' if chroma_success else '❌ Failed'}")
    print(f"   🌱 Seed script: {'✅ Success' if seed_success else '❌ Failed'}")
    print(f"   🔄 Main script: {'✅ Success' if main_success else '❌ Failed'}")
    
    print("=" * 60)
    print("🎉 Multi-space reset process completed!")
    
    return {
        'deleted_pages': all_deleted_pages,
        'failed_deletions': all_failed_deletions,
        'chroma_reset_success': chroma_success,
        'chroma_reset_message': chroma_message,
        'seed_success': seed_success,
        'seed_message': seed_message,
        'main_success': main_success,
        'main_message': main_message,
        'spaces_processed': space_keys
    }LUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_store")

def get_confluence_auth():
    """Get authentication tuple for Confluence API"""
    return (CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)

def get_all_pages_in_space(space_key="SD", limit=100):
    """Get all pages in a Confluence space"""
    all_pages = []
    start = 0
    
    while True:
        try:
            url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
            params = {
                "spaceKey": space_key,
                "type": "page",
                "start": start,
                "limit": limit,
                "expand": "version"
            }
            
            response = requests.get(url, auth=get_confluence_auth(), params=params)
            
            if response.status_code != 200:
                print(f"Error fetching pages: {response.status_code} - {response.text}")
                break
                
            data = response.json()
            pages = data.get('results', [])
            
            if not pages:
                break
                
            all_pages.extend(pages)
            print(f"Retrieved {len(pages)} pages (total: {len(all_pages)})")
            
            # Check if we've reached the end
            if len(pages) < limit:
                break
                
            start += limit
            
        except Exception as e:
            print(f"Error fetching pages: {e}")
            break
    
    return all_pages

def delete_confluence_page(page_id):
    """Delete a Confluence page"""
    try:
        url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
        response = requests.delete(url, auth=get_confluence_auth())
        
        if response.status_code == 204:
            return True, "Page deleted successfully"
        else:
            return False, f"Failed to delete page: {response.status_code} - {response.text}"
    
    except Exception as e:
        return False, f"Error deleting page: {str(e)}"

def delete_all_pages_in_space(space_key="SD"):
    """Delete all pages in a Confluence space"""
    print(f"🔍 Fetching all pages in space '{space_key}'...")
    
    # Get all pages
    all_pages = get_all_pages_in_space(space_key)
    
    if not all_pages:
        print("ℹ️  No pages found in the space.")
        return [], []
    
    print(f"📋 Found {len(all_pages)} pages to delete")
    
    deleted_pages = []
    failed_deletions = []
    
    # Delete each page
    for i, page in enumerate(all_pages, 1):
        page_id = page['id']
        page_title = page['title']
        
        print(f"🗑️  Deleting page {i}/{len(all_pages)}: '{page_title}' (ID: {page_id})")
        
        success, message = delete_confluence_page(page_id)
        
        if success:
            deleted_pages.append({
                'id': page_id,
                'title': page_title,
                'url': f"{CONFLUENCE_BASE_URL}/wiki/spaces/{space_key}/pages/{page_id}"
            })
            print(f"✅ Successfully deleted: '{page_title}'")
        else:
            failed_deletions.append({
                'id': page_id,
                'title': page_title,
                'error': message
            })
            print(f"❌ Failed to delete: '{page_title}' - {message}")
    
    return deleted_pages, failed_deletions

def reset_chroma_database():
    """Reset the Chroma database by deleting all data"""
    try:
        print("🔄 Resetting Chroma database...")
        
        # Check if directory exists
        if os.path.exists(CHROMA_DB_DIR):
            try:
                # Try to create a ChromaDB instance first to properly close any connections
                print("📋 Attempting to properly close ChromaDB connections...")
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
                
                # Try to delete all data from the database first
                try:
                    all_docs = db.get()
                    if all_docs['ids']:
                        db.delete(all_docs['ids'])
                        print("🗑️  Deleted all documents from ChromaDB")
                except Exception as e:
                    print(f"⚠️  Could not delete documents from ChromaDB: {e}")
                
                # Force garbage collection to release file handles
                del db
                del embeddings
                import gc
                gc.collect()
                
                print("🔒 Closed ChromaDB connections")
                
                # Small delay to ensure file handles are released
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️  Could not properly close ChromaDB: {e}")
            
            # Now try to remove the directory
            try:
                # On Windows, use more aggressive deletion
                if os.name == 'nt':  # Windows
                    print("🔧 Using Windows-specific deletion method...")
                    import subprocess
                    
                    # Use Windows rmdir command which can be more aggressive
                    try:
                        subprocess.run(['rmdir', '/s', '/q', CHROMA_DB_DIR], 
                                     shell=True, check=True, capture_output=True)
                        print(f"✅ Deleted Chroma database directory using rmdir: {CHROMA_DB_DIR}")
                    except subprocess.CalledProcessError:
                        # Fallback to Python's shutil
                        print("⚠️  rmdir failed, trying Python shutil...")
                        shutil.rmtree(CHROMA_DB_DIR, ignore_errors=True)
                        print(f"✅ Deleted Chroma database directory using shutil: {CHROMA_DB_DIR}")
                else:
                    # Unix/macOS - use standard method
                    shutil.rmtree(CHROMA_DB_DIR)
                    print(f"✅ Deleted Chroma database directory: {CHROMA_DB_DIR}")
                
            except Exception as e:
                print(f"❌ Error deleting directory: {e}")
                # Try to at least clear the contents
                try:
                    for root, dirs, files in os.walk(CHROMA_DB_DIR, topdown=False):
                        for file in files:
                            try:
                                os.remove(os.path.join(root, file))
                            except:
                                pass
                        for dir in dirs:
                            try:
                                os.rmdir(os.path.join(root, dir))
                            except:
                                pass
                    print("⚠️  Partially cleared ChromaDB directory")
                except Exception as e2:
                    print(f"❌ Could not clear directory contents: {e2}")
                    return False, f"Failed to reset ChromaDB: {str(e)}"
            
            # Recreate empty directory
            os.makedirs(CHROMA_DB_DIR, exist_ok=True)
            print(f"✅ Created new empty Chroma database directory")
            
            return True, "Chroma database reset successfully"
        else:
            print(f"ℹ️  Chroma database directory doesn't exist: {CHROMA_DB_DIR}")
            return True, "Chroma database directory didn't exist"
            
    except Exception as e:
        error_msg = f"Error resetting Chroma database: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def run_seed_script():
    """Run the seed.py script to populate the database"""
    try:
        print("🌱 STEP 3: Running seed.py to populate database...")
        
        # Run seed.py
        result = subprocess.run(
            [sys.executable, "seed.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print("✅ seed.py completed successfully")
            print(f"   Output: {result.stdout.strip()}")
            return True, "Seed script completed successfully"
        else:
            print(f"❌ seed.py failed with return code {result.returncode}")
            print(f"   Error: {result.stderr.strip()}")
            return False, f"Seed script failed: {result.stderr.strip()}"
            
    except Exception as e:
        error_msg = f"Error running seed.py: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def run_main_script():
    """Run the main.py script once to process documents"""
    try:
        print("🔄 STEP 4: Running main.py to process documents...")
        
        # Run main.py
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print("✅ main.py completed successfully")
            print(f"   Output: {result.stdout.strip()}")
            return True, "Main script completed successfully"
        else:
            print(f"❌ main.py failed with return code {result.returncode}")
            print(f"   Error: {result.stderr.strip()}")
            return False, f"Main script failed: {result.stderr.strip()}"
            
    except Exception as e:
        error_msg = f"Error running main.py: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def run_complete_reset_multi_space(space_keys=None):
    """Run complete reset for multiple spaces: delete all Confluence pages, reset Chroma database, run seed.py, then run main.py"""
    if space_keys is None:
        space_keys = ["SD"]  # Default to SD space for backward compatibility
    elif isinstance(space_keys, str):
        space_keys = [space_keys]  # Convert single string to list
    
    print("🚀 Starting complete reset process for multiple spaces...")
    print(f"🌐 Target spaces: {', '.join(space_keys)}")
    print("=" * 60)
    
    # Step 1: Delete all Confluence pages from all spaces
    print("📝 STEP 1: Deleting all Confluence pages from multiple spaces...")
    
    all_deleted_pages = []
    all_failed_deletions = []
    
    for space_key in space_keys:
        print(f"\n🌐 Processing space: {space_key}")
        deleted_pages, failed_deletions = delete_all_pages_in_space(space_key)
        
        all_deleted_pages.extend(deleted_pages)
        all_failed_deletions.extend(failed_deletions)
        
        print(f"   ✅ Deleted from {space_key}: {len(deleted_pages)} pages")
        print(f"   ❌ Failed in {space_key}: {len(failed_deletions)} pages")
    
    print(f"\n📊 Total Confluence deletion results across all spaces:")
    print(f"   ✅ Successfully deleted: {len(all_deleted_pages)} pages")
    print(f"   ❌ Failed to delete: {len(all_failed_deletions)} pages")
    
    # Step 2: Reset Chroma database
    print(f"\n🗃️  STEP 2: Resetting Chroma database...")
    chroma_success, chroma_message = reset_chroma_database()
    
    # Step 3: Run seed.py (only if pages were deleted successfully)
    seed_success = False
    seed_message = "Skipped due to deletion failures"
    
    if len(all_deleted_pages) > 0 or len(all_failed_deletions) == 0:
        print(f"\n🌱 Pages deletion completed, proceeding with seeding...")
        seed_success, seed_message = run_seed_script()
    else:
        print(f"\n⚠️  No pages were deleted, skipping seed.py")
    
    # Step 4: Run main.py (only if seed.py completed successfully)
    main_success = False
    main_message = "Skipped due to seed failure"
    
    if seed_success:
        print(f"\n� Seeding completed, proceeding with main.py...")
        main_success, main_message = run_main_script()
    else:
        print(f"\n⚠️  Seed.py failed or was skipped, skipping main.py")
    
    print(f"\n�📊 Final Results:")
    print(f"   📝 Confluence pages deleted: {len(deleted_pages)}")
    print(f"   📝 Confluence deletion failures: {len(failed_deletions)}")
    print(f"   🗃️  Chroma database reset: {'✅ Success' if chroma_success else '❌ Failed'}")
    print(f"   🌱 Seed script: {'✅ Success' if seed_success else '❌ Failed'}")
    print(f"   🔄 Main script: {'✅ Success' if main_success else '❌ Failed'}")
    
    print("=" * 60)
    print("🎉 Reset process completed!")
    
    return {
        'deleted_pages': deleted_pages,
        'failed_deletions': failed_deletions,
        'chroma_reset_success': chroma_success,
        'chroma_reset_message': chroma_message,
        'seed_success': seed_success,
        'seed_message': seed_message,
        'main_success': main_success,
        'main_message': main_message
    }

if __name__ == "__main__":
    # Interactive mode when run directly
    print("🔥 DocJanitor Reset Tool")
    print("This will delete ALL pages in the Confluence space and reset the Chroma database.")
    print("⚠️  WARNING: This action is irreversible!")
    
    space_key = input("\nEnter Confluence space key (default: SD): ").strip() or "SD"
    
    confirm = input(f"\nAre you sure you want to delete ALL pages in space '{space_key}' and reset the database? (yes/no): ").lower()
    
    if confirm == 'yes':
        result = run_complete_reset(space_key)
        
        print(f"\n📋 Summary:")
        print(f"   Pages deleted: {len(result['deleted_pages'])}")
        print(f"   Deletion failures: {len(result['failed_deletions'])}")
        print(f"   Database reset: {result['chroma_reset_message']}")
        print(f"   Seed script: {result['seed_message']}")
        print(f"   Main script: {result['main_message']}")
        
        if result['failed_deletions']:
            print(f"\n❌ Failed deletions:")
            for failure in result['failed_deletions']:
                print(f"   - {failure['title']}: {failure['error']}")
    else:
        print("❌ Reset cancelled.")
