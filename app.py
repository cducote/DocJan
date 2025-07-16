import streamlit as st
import os
import requests
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_community.document_loaders import ConfluenceLoader
import subprocess

# Simple Document class for creating document objects
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

# Load environment variables
load_dotenv()
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_store")

# Confluence API configuration
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")

# Setup embeddings and Chroma vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'merge_docs' not in st.session_state:
    st.session_state.merge_docs = None
if 'merged_content' not in st.session_state:
    st.session_state.merged_content = ""
if 'manual_edit_mode' not in st.session_state:
    st.session_state.manual_edit_mode = False
if 'confluence_operation_result' not in st.session_state:
    st.session_state.confluence_operation_result = None
if 'reset_confirmation' not in st.session_state:
    st.session_state.reset_confirmation = False
if 'reset_result' not in st.session_state:
    st.session_state.reset_result = None

# Function to merge documents using OpenAI
def merge_documents_with_ai(main_doc, similar_doc):
    try:
        # Read the prompt template
        with open("prompts/merge_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Replace placeholders
        prompt = prompt_template.replace("{{title_a}}", main_doc.metadata.get("title", "Untitled"))
        prompt = prompt.replace("{{title_b}}", similar_doc.metadata.get("title", "Untitled"))
        prompt = prompt.replace("{{url_a}}", main_doc.metadata.get("source", "No URL"))
        prompt = prompt.replace("{{url_b}}", similar_doc.metadata.get("source", "No URL"))
        prompt = prompt.replace("{{content_a}}", main_doc.page_content)
        prompt = prompt.replace("{{content_b}}", similar_doc.page_content)
        
        # Call OpenAI
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        result = llm.invoke(prompt)
        
        return result.content
    except Exception as e:
        return f"Error during merge: {str(e)}"

# Confluence API helper functions
def get_confluence_auth():
    """Get authentication tuple for Confluence API"""
    return (CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)

def extract_page_id_from_url(url):
    """Extract page ID from Confluence URL"""
    if not url:
        return None
    
    # Debug: Print URL to understand format
    print(f"DEBUG: Extracting page ID from URL: {url}")
    
    try:
        # Method 1: Standard viewpage.action URL
        if 'pageId=' in url:
            page_id = url.split('pageId=')[1].split('&')[0]
            print(f"DEBUG: Found pageId in URL: {page_id}")
            return page_id
        
        # Method 2: Modern Confluence URLs with /pages/
        if '/pages/' in url:
            # URL format: https://domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
            parts = url.split('/pages/')
            if len(parts) > 1:
                page_id = parts[1].split('/')[0]
                print(f"DEBUG: Found page ID in modern URL: {page_id}")
                return page_id
        
        # Method 3: API content URL
        if '/rest/api/content/' in url:
            # URL format: https://domain.atlassian.net/rest/api/content/123456
            parts = url.split('/rest/api/content/')
            if len(parts) > 1:
                page_id = parts[1].split('?')[0].split('/')[0]
                print(f"DEBUG: Found page ID in API URL: {page_id}")
                return page_id
        
        # Method 4: Wiki display URL
        if '/display/' in url:
            # This format doesn't contain page ID directly, we need to look for it differently
            # URL format: https://domain.atlassian.net/wiki/display/SPACE/Page+Title
            print(f"DEBUG: Display URL format detected, cannot extract page ID directly")
            return None
        
        print(f"DEBUG: No page ID found in URL format")
        return None
        
    except Exception as e:
        print(f"DEBUG: Error extracting page ID: {e}")
        return None

def get_page_id_by_title(title, space_key="SD"):
    """Get page ID by searching for page title in the space"""
    try:
        # Search for page by title
        url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
        params = {
            "title": title,
            "spaceKey": space_key,
            "expand": "version"
        }
        
        response = requests.get(url, auth=get_confluence_auth(), params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                page_id = data['results'][0]['id']
                print(f"DEBUG: Found page ID by title search: {page_id}")
                return page_id
        
        print(f"DEBUG: Could not find page by title: {title}")
        return None
        
    except Exception as e:
        print(f"DEBUG: Error searching for page by title: {e}")
        return None

def get_page_version(page_id):
    """Get current version of a Confluence page"""
    try:
        url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
        response = requests.get(url, auth=get_confluence_auth())
        if response.status_code == 200:
            data = response.json()
            return data.get('version', {}).get('number', 1)
        return None
    except Exception as e:
        st.error(f"Error getting page version: {str(e)}")
        return None

def update_confluence_page(page_id, new_content, new_title):
    """Update a Confluence page with new content"""
    try:
        # Get current version
        current_version = get_page_version(page_id)
        if current_version is None:
            return False, "Could not get current page version"
        
        # Prepare update payload
        update_data = {
            "version": {
                "number": current_version + 1
            },
            "title": new_title,
            "type": "page",
            "body": {
                "storage": {
                    "value": new_content,
                    "representation": "storage"
                }
            }
        }
        
        # Update the page
        url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
        response = requests.put(
            url, 
            auth=get_confluence_auth(),
            headers={"Content-Type": "application/json"},
            data=json.dumps(update_data)
        )
        
        if response.status_code == 200:
            return True, "Page updated successfully"
        else:
            return False, f"Failed to update page: {response.status_code} - {response.text}"
    
    except Exception as e:
        return False, f"Error updating page: {str(e)}"

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

def convert_markdown_to_confluence_storage(content):
    """Convert content to Confluence storage format"""
    # Since the AI now generates HTML directly, we mainly need to ensure it's clean
    storage_content = content.strip()
    
    # If the content doesn't already have proper HTML structure, wrap it
    if not storage_content.startswith('<'):
        # Wrap plain text in paragraph tags
        storage_content = f"<p>{storage_content}</p>"
    
    # Ensure proper paragraph structure for any remaining plain text
    # Replace double newlines with proper paragraph breaks
    storage_content = storage_content.replace('\n\n', '</p><p>')
    
    # Clean up any remaining single newlines that might break formatting
    storage_content = storage_content.replace('\n', ' ')
    
    return storage_content

def update_chroma_after_merge(main_doc, similar_doc, keep_main=True):
    """Update Chroma database after successful merge to remove duplicate relationships"""
    try:
        # Get the doc_id of the document we're keeping and the one we're removing
        main_doc_id = main_doc.metadata.get('doc_id', '')
        similar_doc_id = similar_doc.metadata.get('doc_id', '')
        
        if not main_doc_id or not similar_doc_id:
            print(f"DEBUG: Missing doc_ids for Chroma update. Main: {main_doc_id}, Similar: {similar_doc_id}")
            return False, "Missing document IDs for Chroma update"
        
        # Determine which document to keep and which to remove
        if keep_main:
            keep_doc_id = main_doc_id
            remove_doc_id = similar_doc_id
        else:
            keep_doc_id = similar_doc_id
            remove_doc_id = main_doc_id
        
        # Get all documents from Chroma
        all_docs = db.get()
        
        if not all_docs['documents']:
            return False, "No documents found in Chroma database"
        
        # Find and update documents that reference the removed document
        updated_count = 0
        documents_to_update = []
        
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', '')
            similar_docs_str = metadata.get('similar_docs', '')
            
            if similar_docs_str and remove_doc_id in similar_docs_str:
                # Remove the deleted document from similar_docs list
                similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
                similar_doc_ids = [id for id in similar_doc_ids if id != remove_doc_id]
                
                # Update the metadata
                updated_metadata = metadata.copy()
                updated_metadata['similar_docs'] = ','.join(similar_doc_ids) if similar_doc_ids else ''
                
                # Store the update information
                documents_to_update.append({
                    'id': all_docs['ids'][i],
                    'document': all_docs['documents'][i],
                    'metadata': updated_metadata
                })
                updated_count += 1
                print(f"DEBUG: Prepared update for document {doc_id} to remove reference to {remove_doc_id}")
        
        # Perform batch update using add (which overwrites existing documents with same IDs)
        if documents_to_update:
            try:
                # First delete the existing documents
                ids_to_update = [item['id'] for item in documents_to_update]
                db.delete(ids_to_update)
                
                # Then add them back with updated metadata
                db.add_documents(
                    documents=[Document(page_content=item['document'], metadata=item['metadata']) 
                             for item in documents_to_update],
                    ids=ids_to_update
                )
                print(f"DEBUG: Successfully updated {len(documents_to_update)} documents via delete+add")
            except Exception as e:
                print(f"DEBUG: Error during batch update: {e}")
                return False, f"Error updating documents: {str(e)}"
        
        # Remove the deleted document from Chroma entirely
        # Find the Chroma ID of the document to remove
        remove_chroma_id = None
        for i, metadata in enumerate(all_docs['metadatas']):
            if metadata.get('doc_id', '') == remove_doc_id:
                remove_chroma_id = all_docs['ids'][i]
                break
        
        if remove_chroma_id:
            db.delete([remove_chroma_id])
            print(f"DEBUG: Removed document {remove_doc_id} from Chroma database")
        
        return True, f"Updated {updated_count} documents and removed merged document from database"
        
    except Exception as e:
        print(f"DEBUG: Error updating Chroma after merge: {e}")
        return False, f"Error updating Chroma database: {str(e)}"

def apply_merge_to_confluence(main_doc, similar_doc, merged_content, keep_main=True):
    """Apply the merge to Confluence: update one page, delete the other"""
    try:
        # Extract page IDs from URLs
        main_page_id = extract_page_id_from_url(main_doc.metadata.get('source'))
        similar_page_id = extract_page_id_from_url(similar_doc.metadata.get('source'))
        
        # If URL extraction failed, try to get page ID by title
        if not main_page_id:
            main_title = main_doc.metadata.get('title')
            if main_title:
                main_page_id = get_page_id_by_title(main_title)
        
        if not similar_page_id:
            similar_title = similar_doc.metadata.get('title')
            if similar_title:
                similar_page_id = get_page_id_by_title(similar_title)
        
        print(f"DEBUG: Main page ID: {main_page_id}, Similar page ID: {similar_page_id}")
        
        if not main_page_id or not similar_page_id:
            return False, f"Could not extract page IDs. Main: {main_page_id}, Similar: {similar_page_id}"
        
        # Determine which page to keep and which to delete
        if keep_main:
            keep_page_id = main_page_id
            delete_page_id = similar_page_id
            keep_title = main_doc.metadata.get('title', 'Merged Document')
        else:
            keep_page_id = similar_page_id
            delete_page_id = main_page_id
            keep_title = similar_doc.metadata.get('title', 'Merged Document')
        
        # Convert content to Confluence storage format
        confluence_content = convert_markdown_to_confluence_storage(merged_content)
        
        # Update the page we're keeping
        update_success, update_message = update_confluence_page(
            keep_page_id, 
            confluence_content, 
            keep_title
        )
        
        if not update_success:
            return False, f"Failed to update page: {update_message}"
        
        # Delete the other page
        delete_success, delete_message = delete_confluence_page(delete_page_id)
        
        if not delete_success:
            return False, f"Updated page but failed to delete duplicate: {delete_message}"
        
        # Update Chroma database to remove duplicate relationships
        chroma_success, chroma_message = update_chroma_after_merge(main_doc, similar_doc, keep_main)
        
        if not chroma_success:
            # Log the error but don't fail the entire operation since Confluence was updated successfully
            print(f"WARNING: Confluence merge succeeded but Chroma update failed: {chroma_message}")
            return True, f"Successfully merged documents. Updated '{keep_title}' and deleted duplicate page. Warning: {chroma_message}"
        
        return True, f"Successfully merged documents. Updated '{keep_title}', deleted duplicate page, and updated database."
    
    except Exception as e:
        return False, f"Error applying merge to Confluence: {str(e)}"

def get_detected_duplicates():
    """Get all document pairs that have been detected as duplicates"""
    try:
        # Get all documents from the database
        all_docs = db.get()
        
        if not all_docs['documents']:
            return []
        
        duplicate_pairs = []
        processed_docs = set()
        
        # Create a mapping from doc_id to index for faster lookup
        doc_id_to_index = {}
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', '')
            if doc_id:
                doc_id_to_index[doc_id] = i
        
        # Process each document
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_id = metadata.get('doc_id', '')
            
            if doc_id in processed_docs:
                continue
            
            content = all_docs['documents'][i]
            
            # Check if this document has similar documents
            similar_docs_str = metadata.get('similar_docs', '')
            if not similar_docs_str:
                continue
                
            similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
            
            # Find the similar documents
            for similar_doc_id in similar_doc_ids:
                if similar_doc_id in processed_docs:
                    continue
                    
                # Find the similar document using the doc_id mapping
                similar_doc_index = doc_id_to_index.get(similar_doc_id)
                
                if similar_doc_index is not None:
                    # Create document objects
                    main_doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    
                    similar_doc = Document(
                        page_content=all_docs['documents'][similar_doc_index],
                        metadata=all_docs['metadatas'][similar_doc_index]
                    )
                    
                    # Calculate similarity score (you can enhance this)
                    similarity_score = 0.8  # Placeholder - you could calculate actual similarity
                    
                    duplicate_pairs.append({
                        'main_doc': main_doc,
                        'similar_doc': similar_doc,
                        'similarity_score': similarity_score,
                        'main_title': metadata.get('title', 'Untitled'),
                        'similar_title': all_docs['metadatas'][similar_doc_index].get('title', 'Untitled')
                    })
                    
                    processed_docs.add(similar_doc_id)
            
            processed_docs.add(doc_id)
        
        return duplicate_pairs
    
    except Exception as e:
        st.error(f"Error getting detected duplicates: {str(e)}")
        return []

# Streamlit UI
st.set_page_config(page_title="DocJanitor - Confluence Duplicate Manager", layout="wide")

# Navigation sidebar
with st.sidebar:
    st.markdown("# **DocJanitor**")
    st.markdown("*Confluence Duplicate Manager*")
    st.markdown("---")
    
    # Navigation buttons
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    if st.button("🔍 Search", use_container_width=True):
        st.session_state.page = 'search'
        st.rerun()
    
    if st.button("📋 Detected Duplicates", use_container_width=True):
        st.session_state.page = 'duplicates'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Current Page")
    st.info(f"📍 {st.session_state.page.title()}")
    
    # Reset section at the bottom
    st.markdown("---")
    st.markdown("### ⚠️ Danger Zone")
    
    # Reset confirmation workflow
    if not st.session_state.reset_confirmation:
        if st.button("🔥 Reset Everything", use_container_width=True, help="Delete ALL pages and reset database"):
            st.session_state.reset_confirmation = True
            st.rerun()
    else:
        st.warning("⚠️ **WARNING**: This will permanently delete ALL pages in the Confluence space and reset the database!")
        st.markdown("This action is **irreversible**. Are you sure?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Reset", use_container_width=True, type="primary"):
                # Run the reset
                with st.spinner("🔥 Resetting everything..."):
                    try:
                        # Import and run the reset function
                        from reset import run_complete_reset
                        result = run_complete_reset()
                        st.session_state.reset_result = result
                        st.session_state.reset_confirmation = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reset failed: {str(e)}")
                        st.session_state.reset_confirmation = False
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.reset_confirmation = False
                st.rerun()
    
    # Show reset results if available
    if st.session_state.reset_result:
        result = st.session_state.reset_result
        st.success("🎉 Reset completed!")
        st.info(f"Pages deleted: {len(result['deleted_pages'])}")
        if result['failed_deletions']:
            st.warning(f"Failed deletions: {len(result['failed_deletions'])}")
        st.info(f"Database: {result['chroma_reset_message']}")
        st.info(f"Seed script: {result.get('seed_message', 'Not run')}")
        st.info(f"Main script: {result.get('main_message', 'Not run')}")
        
        if st.button("Clear Results", key="clear_reset_results"):
            st.session_state.reset_result = None
            st.rerun()

# Page routing
if st.session_state.page == 'dashboard':
    st.title("🏠 Dashboard")
    st.markdown("Welcome to DocJanitor - your Confluence duplicate document manager!")
    
    # Create two columns for the main sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🔍 Search")
        st.markdown("Search for documents and discover potential duplicates using semantic search.")
        
        # Quick search form
        with st.form("quick_search"):
            quick_query = st.text_input("Quick Search", placeholder="Enter search terms...")
            search_submitted = st.form_submit_button("Search", use_container_width=True)
            
            if search_submitted and quick_query:
                # Store search query and switch to search page
                st.session_state.search_query = quick_query
                st.session_state.page = 'search'
                st.rerun()
        
        # Search statistics
        try:
            all_docs = db.get()
            total_docs = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Documents", total_docs)
        except Exception as e:
            st.metric("Total Documents", "Error loading")
    
    with col2:
        st.markdown("## 📋 Detected Duplicates")
        st.markdown("Review and manage document pairs that have been automatically detected as potential duplicates.")
        
        # Get detected duplicates
        duplicate_pairs = get_detected_duplicates()
        
        if duplicate_pairs:
            st.metric("Duplicate Pairs Found", len(duplicate_pairs))
            
            # Simple info message about duplicates with link to duplicates page
            if len(duplicate_pairs) == 1:
                st.info(f"Found {len(duplicate_pairs)} duplicate pair.")
            else:
                st.info(f"Found {len(duplicate_pairs)} duplicate pairs.")
            
            # Button to go to duplicates page
            if st.button("🔍 View All Duplicates", use_container_width=True):
                st.session_state.page = 'duplicates'
                st.rerun()
                
        else:
            st.metric("Duplicate Pairs Found", "0")
            st.info("No duplicate pairs detected yet. Use the search function to find and identify duplicates.")
    
    # Statistics section
    st.markdown("---")
    st.markdown("## 📊 Statistics")
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        try:
            all_docs = db.get()
            total_docs = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Documents", total_docs)
        except:
            st.metric("Total Documents", "Error")
    
    with stat_col2:
        st.metric("Duplicate Pairs", len(duplicate_pairs))
    
    with stat_col3:
        # Calculate documents involved in duplicates
        docs_with_duplicates = len(duplicate_pairs) * 2  # Each pair involves 2 docs
        st.metric("Documents with Duplicates", docs_with_duplicates)
    
    with stat_col4:
        # Calculate potential space saved (placeholder)
        st.metric("Potential Merges", len(duplicate_pairs))

elif st.session_state.page == 'search':
    st.title("🔍 Semantic Search for Confluence")

    # Search configuration sidebar section
    with st.sidebar:
        st.markdown("---")
        st.header("Search Settings")
        
        # Fixed search parameters (no sliders)
        k = 5  # Number of results
        similarity_threshold = 0.7  # Similarity threshold
        search_type = "similarity"  # Default search type

    # Check if there's a search query from dashboard
    initial_query = st.session_state.get('search_query', '')
    if initial_query:
        # Clear the stored query
        st.session_state.search_query = ''
    
    query = st.text_input("Enter your search query:", placeholder="e.g. onboarding, reset password...", key="search_query", value=initial_query)

    # Run search when Enter is pressed or Search button is clicked
    if st.button("Search") or (query and query.strip()):
        if not query.strip():
            st.warning("Please enter a valid query.")
        else:
            with st.spinner("Searching..."):
                # Perform similarity search with fixed parameters
                results = db.similarity_search(query, k=k)
            
            if not results:
                st.info("No documents found for your search query. Try different keywords.")
            else:
                # Group similar documents together
                grouped_results = []
                processed_docs = set()
                
                for doc in results:
                    doc_id = doc.metadata.get('doc_id', '')
                    
                    # Skip if this document was already processed as part of a group
                    if doc_id in processed_docs:
                        continue
                    
                    # Check if this document has similar documents
                    similar_docs_str = doc.metadata.get('similar_docs', '')
                    similar_doc_ids = [id.strip() for id in similar_docs_str.split(',') if id.strip()]
                    
                    # Find similar documents in the current results
                    similar_docs_in_results = []
                    for other_doc in results:
                        other_doc_id = other_doc.metadata.get('doc_id', '')
                        if other_doc_id in similar_doc_ids:
                            similar_docs_in_results.append(other_doc)
                            processed_docs.add(other_doc_id)
                    
                    # Create a group with main document and similar documents
                    group = {
                        'main_doc': doc,
                        'similar_docs': similar_docs_in_results,
                        'total_count': 1 + len(similar_docs_in_results)
                    }
                    
                    grouped_results.append(group)
                    processed_docs.add(doc_id)
                
                st.success(f"Found {len(grouped_results)} relevant document groups ({len(results)} total documents)")
                
                # Show grouped results
                for i, group in enumerate(grouped_results, 1):
                    main_doc = group['main_doc']
                    similar_docs = group['similar_docs']
                    total_count = group['total_count']
                    
                    main_title = main_doc.metadata.get("title", "Untitled Page")
                    main_url = main_doc.metadata.get("source", None)
                    main_content = main_doc.page_content.strip()
                    
                    # Create title with count if there are similar documents
                    if similar_docs:
                        display_title = f"{main_title} ({total_count} similar documents)"
                    else:
                        display_title = main_title
                    
                    with st.expander(f"Result {i}: {display_title}", expanded=(i <= 2)):
                        # Show main document
                        st.markdown("### 📄 Primary Document")
                        if main_url:
                            st.markdown(f"**Source:** [{main_title}]({main_url})")
                        else:
                            st.markdown(f"**Title:** {main_title}")
                        
                        # Show main document content
                        main_content_preview = main_content[:400] + "..." if len(main_content) > 400 else main_content
                        st.markdown("**Content:**")
                        st.write(main_content_preview)
                        
                        # Show similar documents if any
                        if similar_docs:
                            st.markdown("---")
                            st.markdown("### 🔗 Similar Documents")
                            
                            # Add merge button for similar documents
                            if st.button(f"🔀 Merge Documents", key=f"merge_{i}", help="Compare and merge similar documents"):
                                st.session_state.merge_docs = {
                                    'main_doc': main_doc,
                                    'similar_docs': similar_docs
                                }
                                st.session_state.page = 'merge'
                                st.rerun()
                            
                            for j, similar_doc in enumerate(similar_docs, 1):
                                similar_title = similar_doc.metadata.get("title", "Untitled Page")
                                similar_url = similar_doc.metadata.get("source", None)
                                similar_content = similar_doc.page_content.strip()
                                
                                st.markdown(f"**{j}. {similar_title}**")
                                if similar_url:
                                    st.markdown(f"   [View Source]({similar_url})")
                                
                                # Show preview of similar document content
                                similar_content_preview = similar_content[:300] + "..." if len(similar_content) > 300 else similar_content
                                with st.expander(f"Preview: {similar_title}", expanded=False):
                                    st.write(similar_content_preview)
                        
                        # Show metadata for main document
                        if main_doc.metadata:
                            st.markdown("---")
                            st.markdown("**Metadata:**")
                            metadata_display = {k: v for k, v in main_doc.metadata.items() if k not in ['title', 'source', 'similar_docs', 'doc_id']}
                            if metadata_display:
                                st.json(metadata_display)
                        
                        # Option to show full content for main document
                        if len(main_content) > 400:
                            if st.button(f"Show full content", key=f"full_{i}"):
                                st.markdown("**Full Content:**")
                                st.write(main_content)

elif st.session_state.page == 'duplicates':
    st.title("📋 Detected Duplicates")
    st.markdown("Review and manage all document pairs that have been automatically detected as potential duplicates.")
    
    # Get detected duplicates
    duplicate_pairs = get_detected_duplicates()
    
    # Filter section
    st.markdown("### 🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        similarity_filter = st.selectbox(
            "Similarity Score", 
            ["All", "High (>90%)", "Medium (70-90%)", "Low (<70%)"],
            help="Filter duplicates by similarity score"
        )
    
    with col2:
        status_filter = st.selectbox(
            "Status", 
            ["All", "Pending", "Reviewed", "Merged"],
            help="Filter duplicates by processing status"
        )
    
    with col3:
        date_filter = st.selectbox(
            "Date Added", 
            ["All", "Today", "This Week", "This Month"],
            help="Filter duplicates by when they were detected"
        )
    
    with col4:
        sort_by = st.selectbox(
            "Sort By", 
            ["Similarity Score", "Date Added", "Title A-Z", "Title Z-A"],
            help="Sort duplicates by different criteria"
        )
    
    st.markdown("---")
    
    # Results section
    if duplicate_pairs:
        st.markdown(f"### 📊 Found {len(duplicate_pairs)} Duplicate Pairs")
        
        # Create tiles for each duplicate pair
        for i, pair in enumerate(duplicate_pairs):
            with st.container():
                # Create a bordered container for each pair
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 8px; margin-bottom: 16px; background-color: #f9f9f9;">
                """, unsafe_allow_html=True)
                
                # Title row
                col_title, col_actions = st.columns([3, 1])
                
                with col_title:
                    st.markdown(f"**Pair {i+1}:** {pair['main_title']} ↔ {pair['similar_title']}")
                    
                    # Similarity score badge
                    similarity_pct = int(pair['similarity_score'] * 100)
                    if similarity_pct >= 90:
                        badge_color = "green"
                    elif similarity_pct >= 70:
                        badge_color = "orange"
                    else:
                        badge_color = "red"
                    
                    st.markdown(f"""
                    <span style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                        {similarity_pct}% Similar
                    </span>
                    """, unsafe_allow_html=True)
                
                with col_actions:
                    if st.button("🔀 Merge", key=f"merge_dup_{i}", help="Merge these documents"):
                        st.session_state.merge_docs = {
                            'main_doc': pair['main_doc'],
                            'similar_docs': [pair['similar_doc']]
                        }
                        st.session_state.page = 'merge'
                        st.rerun()
                
                # Content preview row
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown(f"**📄 {pair['main_title']}**")
                    main_content = pair['main_doc'].page_content
                    preview = main_content[:150] + "..." if len(main_content) > 150 else main_content
                    st.text(preview)
                    
                    # Show source if available
                    main_source = pair['main_doc'].metadata.get('source', '')
                    if main_source:
                        st.markdown(f"[🔗 View Source]({main_source})")
                
                with col_right:
                    st.markdown(f"**📄 {pair['similar_title']}**")
                    similar_content = pair['similar_doc'].page_content
                    preview = similar_content[:150] + "..." if len(similar_content) > 150 else similar_content
                    st.text(preview)
                    
                    # Show source if available
                    similar_source = pair['similar_doc'].metadata.get('source', '')
                    if similar_source:
                        st.markdown(f"[🔗 View Source]({similar_source})")
                
                # Action buttons row
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                
                with col_btn1:
                    if st.button("👀 Preview", key=f"preview_{i}", help="Preview both documents"):
                        st.info("Preview functionality coming soon!")
                
                with col_btn2:
                    if st.button("❌ Not Duplicate", key=f"not_dup_{i}", help="Mark as not duplicate"):
                        st.info("Not duplicate functionality coming soon!")
                
                with col_btn3:
                    if st.button("⏭️ Skip", key=f"skip_{i}", help="Skip for now"):
                        st.info("Skip functionality coming soon!")
                
                with col_btn4:
                    if st.button("📝 Details", key=f"details_{i}", help="View detailed comparison"):
                        st.info("Details functionality coming soon!")
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("🔍 No duplicate pairs detected yet. Use the search function to find and identify duplicates.")
        
        # Add helpful guidance
        st.markdown("### 💡 Tips for Finding Duplicates")
        st.markdown("- Use the **Search** page to perform semantic searches")
        st.markdown("- Similar documents will be automatically grouped together")
        st.markdown("- The system learns from your interactions to improve detection")

elif st.session_state.page == 'merge':
    st.title("🔀 Document Merge Tool")
    
    # Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back", use_container_width=True):
            # Go back to the previous page (dashboard or search)
            st.session_state.page = 'dashboard'
            st.rerun()
    
    if st.session_state.merge_docs:
        main_doc = st.session_state.merge_docs['main_doc']
        similar_docs = st.session_state.merge_docs['similar_docs']
        
        st.markdown("### Compare and merge similar documents")
        st.markdown("---")
        
        # Side-by-side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Primary Document")
            main_title = main_doc.metadata.get("title", "Untitled Page")
            main_content = main_doc.page_content.strip()
            
            st.markdown(f"**Title:** {main_title}")
            st.markdown("**Content:**")
            st.text_area("Primary Document Content", main_content, height=400, disabled=True, key="main_content")
        
        with col2:
            st.markdown("### 🔗 Similar Document")
            if similar_docs:
                # For now, show the first similar document
                similar_doc = similar_docs[0]
                similar_title = similar_doc.metadata.get("title", "Untitled Page")
                similar_content = similar_doc.page_content.strip()
                
                st.markdown(f"**Title:** {similar_title}")
                st.markdown("**Content:**")
                st.text_area("Similar Document Content", similar_content, height=400, disabled=True, key="similar_content")
        
        # Merge controls
        st.markdown("---")
        st.markdown("### 🔧 Merge Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Auto-Merge with AI", use_container_width=True):
                with st.spinner("Merging documents with AI..."):
                    if similar_docs:
                        merged_result = merge_documents_with_ai(main_doc, similar_docs[0])
                        st.session_state.merged_content = merged_result
                        st.success("Documents merged successfully!")
                        st.rerun()
                    else:
                        st.error("No similar documents found to merge.")
        
        with col2:
            if st.button("✏️ Manual Edit", use_container_width=True):
                st.session_state.manual_edit_mode = True
                st.rerun()
        
        with col3:
            if st.button("💾 Save Merged Document", use_container_width=True):
                if st.session_state.merged_content:
                    st.success("Merged document saved! (Implementation pending)")
                else:
                    st.warning("No merged content to save. Please merge documents first.")
        
        # Display merged content
        st.markdown("### 📝 Merged Document Preview")
        
        # Check if we're in manual edit mode
        if 'manual_edit_mode' in st.session_state and st.session_state.manual_edit_mode:
            # Manual edit mode - editable text area
            st.markdown("**Manual Edit Mode** - You can edit the merged content below:")
            edited_content = st.text_area(
                "Edit Merged Content", 
                value=st.session_state.merged_content or "Start editing here...", 
                height=300, 
                key="manual_edit_area"
            )
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Save Changes", use_container_width=True):
                    st.session_state.merged_content = edited_content
                    st.session_state.manual_edit_mode = False
                    st.success("Changes saved!")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Cancel Edit", use_container_width=True):
                    st.session_state.manual_edit_mode = False
                    st.rerun()
        else:
            # Display mode - show merged content
            if st.session_state.merged_content:
                st.text_area("Merged Content", st.session_state.merged_content, height=300, disabled=True)
            else:
                st.text_area("Merged Content", "AI-generated merged content will appear here...", height=300, disabled=True)
        
        # Confluence integration section
        if st.session_state.merged_content:
            st.markdown("---")
            st.markdown("### 🔄 Apply to Confluence")
            
            # Debug information
            with st.expander("🔍 Debug Information", expanded=False):
                st.markdown("**Main Document:**")
                st.code(f"Title: {main_doc.metadata.get('title', 'N/A')}")
                st.code(f"Source: {main_doc.metadata.get('source', 'N/A')}")
                
                if similar_docs:
                    st.markdown("**Similar Document:**")
                    st.code(f"Title: {similar_docs[0].metadata.get('title', 'N/A')}")
                    st.code(f"Source: {similar_docs[0].metadata.get('source', 'N/A')}")
            
            # Page selection
            st.markdown("**Choose which page to keep:**")
            col_main, col_similar = st.columns(2)
            
            with col_main:
                main_title = main_doc.metadata.get('title', 'Untitled Page')
                main_url = main_doc.metadata.get('source', '')
                if st.button(f"📄 Keep Primary: {main_title}", use_container_width=True, key="keep_main"):
                    keep_main = True
                    st.session_state.selected_page = 'main'
                    
                    with st.spinner("Applying merge to Confluence..."):
                        success, message = apply_merge_to_confluence(
                            main_doc, 
                            similar_docs[0], 
                            st.session_state.merged_content, 
                            keep_main=True
                        )
                        st.session_state.confluence_operation_result = (success, message)
                        st.rerun()
            
            with col_similar:
                if similar_docs:
                    similar_title = similar_docs[0].metadata.get('title', 'Untitled Page')
                    similar_url = similar_docs[0].metadata.get('source', '')
                    if st.button(f"🔗 Keep Similar: {similar_title}", use_container_width=True, key="keep_similar"):
                        keep_main = False
                        st.session_state.selected_page = 'similar'
                        
                        with st.spinner("Applying merge to Confluence..."):
                            success, message = apply_merge_to_confluence(
                                main_doc, 
                                similar_docs[0], 
                                st.session_state.merged_content, 
                                keep_main=False
                            )
                            st.session_state.confluence_operation_result = (success, message)
                            st.rerun()
            
            # Show operation result
            if st.session_state.confluence_operation_result:
                success, message = st.session_state.confluence_operation_result
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
                
                # Clear result after showing
                if st.button("🔄 Clear Result", key="clear_result"):
                    st.session_state.confluence_operation_result = None
                    st.rerun()
            
            # Warning about the operation
            st.warning("⚠️ **Important**: This will permanently update one page and delete the other in Confluence. Make sure you have the necessary permissions and have reviewed the merged content.")
        
        else:
            st.info("💡 Generate merged content first to enable Confluence integration.")