import os
import requests
import json
import time
import sys
from dotenv import load_dotenv

# Fix for SQLite3 version compatibility on cloud platforms
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import shutil
import subprocess

# Load environment variables
load_dotenv()

# Confluence API configuration
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
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

def delete_all_pages_in_spaces(space_keys):
    """Delete all pages in multiple Confluence spaces"""
    if isinstance(space_keys, str):
        space_keys = [space_keys]
    
    all_deleted_pages = []
    all_failed_deletions = []
    
    for space_key in space_keys:
        print(f"[*] Processing space: {space_key}")
        deleted_pages, failed_deletions = delete_all_pages_in_space(space_key)
        
        # Add space info to each result
        for page in deleted_pages:
            page['space'] = space_key
        for page in failed_deletions:
            page['space'] = space_key
            
        all_deleted_pages.extend(deleted_pages)
        all_failed_deletions.extend(failed_deletions)
        
        print(f"[*] Space {space_key}: {len(deleted_pages)} deleted, {len(failed_deletions)} failed")
    
    return all_deleted_pages, all_failed_deletions


def delete_all_pages_in_space(space_key="SD"):
    """Delete all pages in a Confluence space"""
    print(f"[*] Fetching all pages in space '{space_key}'...")
    
    # Get all pages
    all_pages = get_all_pages_in_space(space_key)
    
    if not all_pages:
        print("[i] No pages found in the space.")
        return [], []
    
    print(f"[*] Found {len(all_pages)} pages to delete")
    
    deleted_pages = []
    failed_deletions = []
    
    # Delete each page
    for i, page in enumerate(all_pages, 1):
        page_id = page['id']
        page_title = page['title']
        
        print(f"[*] Deleting page {i}/{len(all_pages)}: '{page_title}' (ID: {page_id})")
        
        success, message = delete_confluence_page(page_id)
        
        if success:
            deleted_pages.append({
                'id': page_id,
                'title': page_title,
                'url': f"{CONFLUENCE_BASE_URL}/wiki/spaces/{space_key}/pages/{page_id}"
            })
            print(f"[+] Successfully deleted: '{page_title}'")
        else:
            failed_deletions.append({
                'id': page_id,
                'title': page_title,
                'error': message
            })
            print(f"[-] Failed to delete: '{page_title}' - {message}")
    
    return deleted_pages, failed_deletions

def reset_chroma_database():
    """Reset the Chroma database by deleting all data"""
    try:
        print("[*] Resetting Chroma database...")
        
        # Import here to avoid circular import issues
        if os.path.exists(CHROMA_DB_DIR):
            try:
                # Try to create a ChromaDB instance first to properly close any connections
                print("[*] Attempting to properly close ChromaDB connections...")
                
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
                
                # Try to delete all documents first
                try:
                    all_docs = db.get()
                    if all_docs and all_docs.get('ids'):
                        db.delete(ids=all_docs['ids'])
                        print("[*] Deleted all documents from ChromaDB")
                except Exception as e:
                    print(f"[!] Could not delete documents from ChromaDB: {e}")
                
                # Close the database connection
                try:
                    # Access the underlying client and close it
                    if hasattr(db, '_client'):
                        print("[*] Closing ChromaDB client...")
                        db._client.reset()
                    print("[*] Closed ChromaDB connections")
                    
                    # Small delay to ensure connections are closed
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"[!] Could not properly close ChromaDB: {e}")
                    
            except Exception as e:
                print(f"[!] Error with ChromaDB operations: {e}")
            
            # Now try to delete the directory
            try:
                print(f"[*] Attempting to delete Chroma database directory: {CHROMA_DB_DIR}")
                if os.name == 'nt':  # Windows
                    try:
                        subprocess.run(['rmdir', '/s', '/q', CHROMA_DB_DIR], 
                                     check=True, shell=True)
                        print(f"[+] Deleted Chroma database directory using rmdir: {CHROMA_DB_DIR}")
                    except subprocess.CalledProcessError:
                        # Fallback to shutil
                        shutil.rmtree(CHROMA_DB_DIR, ignore_errors=True)
                        print(f"[+] Deleted Chroma database directory using shutil: {CHROMA_DB_DIR}")
                else:  # Unix/Linux/MacOS
                    shutil.rmtree(CHROMA_DB_DIR, ignore_errors=True)
                    print(f"[+] Deleted Chroma database directory: {CHROMA_DB_DIR}")
                    
            except Exception as e:
                print(f"[!] Could not delete Chroma database directory: {e}")
                return False, f"Failed to delete Chroma database directory: {str(e)}"
        else:
            print("[*] Chroma database directory does not exist, skipping...")
        
        return True, "Chroma database reset successfully"
    
    except Exception as e:
        print(f"[!] Unexpected error resetting Chroma database: {e}")
        return False, f"Failed to reset Chroma database: {str(e)}"


def cleanup_merge_operations():
    """Clean up the merge operations history file"""
    try:
        merge_ops_file = "merge_operations.json"
        if os.path.exists(merge_ops_file):
            os.remove(merge_ops_file)
            print(f"[+] Deleted merge operations history file: {merge_ops_file}")
            return True, "Merge operations history cleared successfully"
        else:
            print("[*] Merge operations history file does not exist, skipping...")
            return True, "No merge operations history to clear"
    except Exception as e:
        print(f"[!] Error cleaning up merge operations history: {e}")
        return False, f"Failed to clean up merge operations: {str(e)}"

def run_seed_script():
    """Run the seed.py script to populate the database"""
    try:
        print("[*] STEP 3: Running seed.py to populate database...")
        
        # Run seed.py
        result = subprocess.run(
            [sys.executable, "seed.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print("[+] seed.py completed successfully")
            print(f"    Output: {result.stdout.strip()}")
            return True, "Seed script completed successfully"
        else:
            print(f"[-] seed.py failed with return code {result.returncode}")
            print(f"    Error: {result.stderr.strip()}")
            return False, f"Seed script failed: {result.stderr.strip()}"
            
    except Exception as e:
        error_msg = f"Error running seed.py: {str(e)}"
        print(f"[-] {error_msg}")
        return False, error_msg

def run_complete_reset(space_keys=None):
    """Run complete reset: delete all Confluence pages from multiple spaces, reset Chroma database, run seed.py"""
    # Default to the spaces used by seed.py
    if space_keys is None:
        space_keys = ["SD", "~70121465f64cb86d84c92b0bdbc36762f880c"]  # SD and PERSONAL spaces
    elif isinstance(space_keys, str):
        space_keys = [space_keys]
    
    print("[*] Starting complete reset process...")
    print(f"[*] Target spaces: {space_keys}")
    print("=" * 60)
    
    # Step 1: Delete all Confluence pages from multiple spaces
    print("[*] STEP 1: Deleting all Confluence pages from multiple spaces...")
    deleted_pages, failed_deletions = delete_all_pages_in_spaces(space_keys)
    
    print(f"\n[*] Confluence deletion results:")
    for space_key in space_keys:
        space_deleted = [p for p in deleted_pages if p.get('space') == space_key]
        space_failed = [p for p in failed_deletions if p.get('space') == space_key]
        print(f"    [{space_key}] Successfully deleted: {len(space_deleted)} pages")
        print(f"    [{space_key}] Failed to delete: {len(space_failed)} pages")
    print(f"    [TOTAL] Successfully deleted: {len(deleted_pages)} pages")
    print(f"    [TOTAL] Failed to delete: {len(failed_deletions)} pages")
    
    # Step 2: Reset Chroma database
    print(f"\n[*] STEP 2: Resetting Chroma database...")
    chroma_success, chroma_message = reset_chroma_database()
    
    # Step 2.5: Clean up merge operations history
    print(f"\n[*] STEP 2.5: Cleaning up merge operations history...")
    merge_cleanup_success, merge_cleanup_message = cleanup_merge_operations()
    
    # Step 3: Run seed.py (only if pages were deleted successfully)
    seed_success = False
    seed_message = "Skipped due to deletion failures"
    
    if len(deleted_pages) > 0 or len(failed_deletions) == 0:
        print(f"\n[*] Pages deletion completed, proceeding with seeding...")
        seed_success, seed_message = run_seed_script()
    else:
        print(f"\n[!] No pages were deleted, skipping seed.py")
    
    print(f"\n[*] Final Results:")
    print(f"    [*] Confluence pages deleted: {len(deleted_pages)}")
    print(f"    [*] Confluence deletion failures: {len(failed_deletions)}")
    print(f"    [*] Chroma database reset: {'Success' if chroma_success else 'Failed'}")
    print(f"    [*] Merge operations cleanup: {'Success' if merge_cleanup_success else 'Failed'}")
    print(f"    [*] Seed script: {'Success' if seed_success else 'Failed'}")
    
    print("=" * 60)
    print("[*] Reset process completed!")
    
    return {
        'success': True,
        'deleted_pages': deleted_pages,
        'failed_deletions': failed_deletions,
        'chroma_reset_success': chroma_success,
        'chroma_reset_message': chroma_message,
        'merge_cleanup_success': merge_cleanup_success,
        'merge_cleanup_message': merge_cleanup_message,
        'seed_success': seed_success,
        'seed_message': seed_message,
        'details': f"Deleted {len(deleted_pages)} pages from {len(space_keys)} spaces, reset database, cleaned merge history, ran seed script"
    }

if __name__ == "__main__":
    # Interactive mode when run directly
    print("[*] DocJanitor Reset Tool")
    print("This will delete ALL pages in the Confluence spaces and reset the Chroma database.")
    print("[!] WARNING: This action is irreversible!")
    
    print("\nAvailable options:")
    print("1. Reset both SD and PERSONAL spaces (default)")
    print("2. Reset only SD space")
    print("3. Reset only PERSONAL space")
    print("4. Custom space selection")
    
    choice = input("\nEnter your choice (1-4, default: 1): ").strip() or "1"
    
    if choice == "1":
        space_keys = ["SD", "~70121465f64cb86d84c92b0bdbc36762f880c"]
        space_names = "SD and PERSONAL"
    elif choice == "2":
        space_keys = ["SD"]
        space_names = "SD"
    elif choice == "3":
        space_keys = ["~70121465f64cb86d84c92b0bdbc36762f880c"]
        space_names = "PERSONAL"
    elif choice == "4":
        custom_spaces = input("Enter space keys separated by commas: ").strip()
        if custom_spaces:
            space_keys = [s.strip() for s in custom_spaces.split(",")]
            space_names = ", ".join(space_keys)
        else:
            print("No spaces provided. Using default (SD and PERSONAL).")
            space_keys = ["SD", "~70121465f64cb86d84c92b0bdbc36762f880c"]
            space_names = "SD and PERSONAL"
    else:
        print("Invalid choice. Using default (SD and PERSONAL).")
        space_keys = ["SD", "~70121465f64cb86d84c92b0bdbc36762f880c"]
        space_names = "SD and PERSONAL"
    
    confirm = input(f"\nAre you sure you want to delete ALL pages in {space_names} space(s) and reset the database? (yes/no): ").lower()
    
    if confirm == 'yes':
        result = run_complete_reset(space_keys)
        
        print(f"\n[*] Summary:")
        print(f"    Pages deleted: {len(result['deleted_pages'])}")
        print(f"    Deletion failures: {len(result['failed_deletions'])}")
        print(f"    Database reset: {result['chroma_reset_message']}")
        print(f"    Seed script: {result['seed_message']}")
        
        if result['failed_deletions']:
            print(f"\n[-] Failed deletions:")
            for failure in result['failed_deletions']:
                space_info = f" [{failure.get('space', 'Unknown')}]" if 'space' in failure else ""
                print(f"    - {failure['title']}{space_info}: {failure['error']}")
    else:
        print("[-] Reset cancelled.")


def run_complete_reset_multi_space(spaces_dict=None):
    """
    Delete all pages from multiple spaces and reset ChromaDB.
    
    Args:
        spaces_dict (dict): Dictionary of space keys and names to reset.
                           If None, uses session state selected_spaces.
    """
    if spaces_dict is None:
        import streamlit as st
        if hasattr(st.session_state, 'selected_spaces'):
            spaces_dict = st.session_state.selected_spaces
        else:
            print("❌ No spaces selected for reset")
            return False
    
    if not spaces_dict:
        print("❌ No spaces provided for reset")
        return False
    
    print(f"🗑️ Starting complete reset for {len(spaces_dict)} spaces...")
    
    # Delete pages from all selected spaces
    all_deleted_pages = []
    all_failed_deletions = []
    
    for space_key, space_name in spaces_dict.items():
        print(f"\n📁 Processing space: {space_name} ({space_key})")
        deleted_pages, failed_deletions = delete_all_pages_in_space(space_key)
        
        all_deleted_pages.extend(deleted_pages)
        all_failed_deletions.extend(failed_deletions)
        
        if failed_deletions:
            print(f"⚠️ {len(failed_deletions)} pages failed to delete from {space_name}")
        else:
            print(f"✅ Successfully deleted {len(deleted_pages)} pages from {space_name}")
    
    # Reset ChromaDB
    print("\n🔄 Resetting ChromaDB...")
    chroma_success, chroma_message = reset_chroma_database()
    print(f"ChromaDB reset: {chroma_message}")
    
    # Return success if no failures occurred
    success = len(all_failed_deletions) == 0 and chroma_success
    
    if success:
        print(f"✅ Complete multi-space reset successful!")
        print(f"   Total pages deleted: {len(all_deleted_pages)}")
        print(f"   Spaces processed: {len(spaces_dict)}")
        return True
    else:
        print("❌ Multi-space reset completed with some errors")
        print(f"   Pages deleted: {len(all_deleted_pages)}")
        print(f"   Failed deletions: {len(all_failed_deletions)}")
        return False