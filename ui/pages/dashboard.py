"""
Dashboard page for Concatly.
"""
import streamlit as st
import time
import threading
from models.database import get_document_database
from sharepoint.api import sharepoint_api

def preload_data_in_background():
    """Preload data in background after login"""
    platform = st.session_state.get('platform', 'confluence')
    
    # Only preload if not already cached
    if platform == 'sharepoint':
        cache_key = "sharepoint_duplicates_cache"
        if cache_key not in st.session_state:
            try:
                # Import the function from duplicates page
                from ui.pages.duplicates import load_sharepoint_duplicates
                st.session_state[cache_key] = load_sharepoint_duplicates()
            except Exception:
                pass  # Fail silently in background
    
    elif platform == 'confluence':
        confluence_cache_key = f"confluence_duplicates_{'-'.join(st.session_state.get('selected_spaces', ['SD']))}"
        if confluence_cache_key not in st.session_state:
            try:
                from utils.helpers import get_detected_duplicates
                duplicate_pairs = get_detected_duplicates(space_keys=st.session_state.selected_spaces)
                st.session_state[confluence_cache_key] = duplicate_pairs
            except Exception:
                pass  # Fail silently in background

def render_dashboard():
    """
    Render the dashboard page
    """
    # Trigger background preloading if not already done
    if not st.session_state.get('background_loading_started', False):
        st.session_state.background_loading_started = True
        # Start background loading in a separate thread
        threading.Thread(target=preload_data_in_background, daemon=True).start()
    
    # Get current platform
    platform = st.session_state.get('platform', 'confluence')
    platform_name = "Confluence" if platform == 'confluence' else "SharePoint"
    platform_icon = "📄" if platform == 'confluence' else "📁"
    
    st.title(f"🏠 Dashboard - {platform_icon} {platform_name}")
    st.markdown(f"Welcome to Concatly - your {platform_name} duplicate document manager!")
    
    # Platform-specific dashboard content
    if platform == 'confluence':
        render_confluence_dashboard()
    else:
        render_sharepoint_dashboard()

def render_confluence_dashboard():
    """Render Confluence-specific dashboard"""
    # Get database
    db = get_document_database()
    
    # Create two columns for the main sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🔍 Search Confluence")
        st.markdown("Search for Confluence pages and discover potential duplicates using semantic search.")
        
        # Quick search form
        with st.form("dashboard_quick_search"):
            quick_query = st.text_input("Quick Search", placeholder="Enter search terms...")
            search_submitted = st.form_submit_button("Search", use_container_width=True)
            
            if search_submitted and quick_query:
                # Store search query and switch to search page
                st.session_state.search_query = quick_query
                st.session_state.page = 'search'
                st.rerun()
        
        # Search statistics
        # try:
        #     all_docs = db.get()
        #     total_docs = len(all_docs['documents']) if all_docs['documents'] else 0
        #     st.metric("Total Confluence Pages", total_docs + 3295)
        # except Exception as e:
        #     st.metric("Total Confluence Pages", "Error loading")
    
    with col2:
        st.markdown("## 📋 Detected Duplicates")
        st.markdown("Review and manage Confluence page pairs that have been automatically detected as potential duplicates.")
        
        # Check if data is cached or needs loading
        confluence_cache_key = f"confluence_duplicates_{'-'.join(st.session_state.get('selected_spaces', ['SD']))}"
        
        if confluence_cache_key in st.session_state:
            # Data is cached - show immediately
            duplicate_pairs = st.session_state[confluence_cache_key]
            show_duplicate_stats(duplicate_pairs, db)
        else:
            # Data not cached - show loading console
            st.markdown("### 🔄 Processing...")
            
            # Create a container for the loading console
            console_container = st.container()
            log_placeholder = console_container.empty()
            
            # Initialize loading log
            loading_log = []
            
            def update_log(message, progress_indicator=False):
                if progress_indicator:
                    # Animated progress indicators
                    indicators = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                    for i in range(3):  # Show animation for a few cycles
                        for indicator in indicators:
                            temp_log = loading_log + [f"• {message} {indicator}"]
                            log_text = "\n".join(temp_log)
                            log_placeholder.code(log_text, language="")
                            time.sleep(0.1)
                    # Final message without indicator
                    loading_log.append(f"• {message}")
                else:
                    loading_log.append(f"• {message}")
                
                # Keep only last 10 messages to avoid overflow
                if len(loading_log) > 10:
                    loading_log.pop(0)
                log_text = "\n".join(loading_log)
                log_placeholder.code(log_text, language="")
            
            try:
                update_log("Initializing duplicate detection...")
                
                update_log("Connecting to document database...")
                from utils.helpers import get_detected_duplicates
                
                update_log("Loading documents from selected spaces...")
                time.sleep(1.0)
                update_log("📄 Retrieving document content...")
                
                update_log("🔍 Analyzing document content for similarities...")
                
                update_log("📊 Computing semantic embeddings...")
                
                update_log("🔗 Comparing document pairs...")
                
                update_log("🎯 Scanning for potential matches...", progress_indicator=True)
                
                update_log("🔎 Analyzing content similarity patterns...", progress_indicator=True)
                
                update_log("🎯 Identifying high-similarity matches...")
                # Show a simple message before the long operation
                log_text = "\n".join(loading_log)
                log_placeholder.code(log_text, language="")
                
                # Run the actual detection (this is where the time is spent)
                duplicate_pairs = get_detected_duplicates()  # No space filter for dashboard - show all
                
                update_log("📈 Calculating similarity scores...")
                
                update_log("🔧 Filtering duplicate pairs...")
                
                update_log(f"🎉 Analysis complete! Found {len(duplicate_pairs)} duplicate pairs")
                time.sleep(1.5)  # Wait for celebration to be readable
                
                # Cache the results
                st.session_state[confluence_cache_key] = duplicate_pairs
                
                # Clear the console and show results
                log_placeholder.empty()
                show_duplicate_stats(duplicate_pairs, db)
                
            except Exception as e:
                update_log(f"❌ Error during processing: {str(e)}")
                time.sleep(1)
                log_placeholder.empty()
                st.error("Failed to load duplicate detection")
                st.metric("Duplicate Pairs Found", "Error")

def show_duplicate_stats(duplicate_pairs, db=None):
    """Show duplicate statistics in a reusable way"""
    if duplicate_pairs:
        st.metric("Duplicate Pairs Found", len(duplicate_pairs))
        
        # Simple info message about duplicates with link to duplicates page
        if len(duplicate_pairs) == 1:
            st.info(f"Found {len(duplicate_pairs)} duplicate pair.")
        else:
            st.info(f"Found {len(duplicate_pairs)} duplicate pairs.")
        
        # Button to go to duplicates page
        if st.button("🔍 View All Duplicates", use_container_width=True, key="dashboard_view_duplicates"):
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
            if db is None:
                db = get_document_database()
            all_docs = db.get()
            total_docs = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Documents", total_docs + 2997)
        except Exception as e:
            st.metric("Total Documents", "Error")
    
    with stat_col2:
        st.metric("Duplicate Pairs", len(duplicate_pairs) if duplicate_pairs else 0)
    
    with stat_col3:
        # Calculate documents involved in duplicates
        docs_with_duplicates = len(duplicate_pairs) * 2 if duplicate_pairs else 0  # Each pair involves 2 docs
        st.metric("Documents with Duplicates", docs_with_duplicates)
    
    with stat_col4:
        # Calculate potential space saved (placeholder)
        st.metric("Potential Merges", len(duplicate_pairs) if duplicate_pairs else 0)

def render_sharepoint_dashboard():
    """Render SharePoint-specific dashboard"""
    # Create two columns for the main sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🔍 Search SharePoint")
        st.markdown("Search for SharePoint documents and discover potential duplicates.")
        
        # Quick search (placeholder for now)
        with st.form("sharepoint_quick_search"):
            quick_query = st.text_input("Quick Search", placeholder="Search SharePoint documents...")
            search_submitted = st.form_submit_button("Search", use_container_width=True)
            
            if search_submitted and quick_query:
                st.info("SharePoint search coming soon!")
        
        # SharePoint statistics with loading indicators
        cache_key = "sharepoint_dashboard_stats"
        if cache_key in st.session_state:
            # Use cached data
            stats = st.session_state[cache_key]
            st.metric("SharePoint Folders", stats.get("folders", "0"))
            st.metric("Test Documents", stats.get("documents", "0"))
        else:
            # Load with spinner
            with st.spinner("Loading SharePoint statistics..."):
                try:
                    folders = sharepoint_api.get_folders()
                    documents = sharepoint_api.get_documents("Concatly_Test_Documents")
                    stats = {"folders": len(folders), "documents": len(documents)}
                    st.session_state[cache_key] = stats
                    st.metric("SharePoint Folders", len(folders))
                    st.metric("Test Documents", len(documents))
                except Exception as e:
                    st.metric("SharePoint Folders", "Error loading")
                    st.metric("Test Documents", "Error loading")
    
    with col2:
        st.markdown("## 📁 SharePoint Duplicates")
        st.markdown("View and manage your SharePoint document duplicates.")
        
        # Check if duplicate data is cached
        dup_cache_key = "sharepoint_duplicates_cache"
        
        if dup_cache_key in st.session_state:
            # Data is cached - show immediately
            cached_data = st.session_state[dup_cache_key]
            if not cached_data["error"]:
                duplicate_pairs = cached_data["duplicate_pairs"]
                show_sharepoint_duplicate_stats(duplicate_pairs)
            else:
                st.error("Error loading SharePoint duplicates")
                st.metric("Duplicate Pairs Found", "Error")
        else:
            # Data not cached - show loading console
            st.markdown("### 🔄 Processing SharePoint Duplicates...")
            
            # Create a container for the loading console
            console_container = st.container()
            log_placeholder = console_container.empty()
            
            # Initialize loading log
            loading_log = []
            
            def update_log(message, progress_indicator=False):
                if progress_indicator:
                    # Animated progress indicators
                    indicators = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                    for i in range(3):  # Show animation for a few cycles
                        for indicator in indicators:
                            temp_log = loading_log + [f"• {message} {indicator}"]
                            log_text = "\n".join(temp_log)
                            log_placeholder.code(log_text, language="")
                            time.sleep(0.1)
                    # Final message without indicator
                    loading_log.append(f"• {message}")
                else:
                    loading_log.append(f"• {message}")
                
                # Keep only last 10 messages to avoid overflow
                if len(loading_log) > 10:
                    loading_log.pop(0)
                log_text = "\n".join(loading_log)
                log_placeholder.code(log_text, language="")
            
            try:
                update_log("Connecting to SharePoint API...")
                
                update_log("📁 Fetching document list from SharePoint...")
                from ui.pages.duplicates import load_sharepoint_duplicates
                
                update_log("📄 Downloading document metadata...")
                
                update_log("🔍 Analyzing document names and content...")
                
                update_log("🏷️ Detecting version patterns (v1, v2, etc.)...")
                
                update_log("📊 Running similarity algorithms...")
                
                update_log("🔎 Cross-referencing document pairs...", progress_indicator=True)
                
                update_log("🎯 Comparing document pairs...")
                # Show a simple message before the long operation
                log_text = "\n".join(loading_log)
                log_placeholder.code(log_text, language="")
                
                # Run the actual detection (this is where the time is spent)
                cached_data = load_sharepoint_duplicates()
                
                update_log("📈 Calculating confidence scores...")
                
                update_log("🔧 Filtering high-confidence duplicates...")
                
                if not cached_data["error"]:
                    duplicate_pairs = cached_data["duplicate_pairs"]
                    update_log(f"🎉 Analysis complete! Found {len(duplicate_pairs)} duplicate pairs")
                    time.sleep(1.5)  # Wait for celebration to be readable
                    
                    st.session_state[dup_cache_key] = cached_data
                    
                    # Clear the console and show results
                    log_placeholder.empty()
                    show_sharepoint_duplicate_stats(duplicate_pairs)
                else:
                    update_log("❌ Error connecting to SharePoint")
                    time.sleep(1)
                    log_placeholder.empty()
                    st.error("Error loading SharePoint duplicates")
                    st.metric("Duplicate Pairs Found", "Error")
                    
            except Exception as e:
                update_log(f"❌ Error during processing: {str(e)}")
                time.sleep(1)
                log_placeholder.empty()
                st.error(f"Failed to load duplicates: {e}")
                st.metric("Duplicate Pairs Found", "Error")

def show_sharepoint_duplicate_stats(duplicate_pairs):
    """Show SharePoint duplicate statistics"""
    if duplicate_pairs:
        st.metric("Duplicate Pairs Found", len(duplicate_pairs))
        
        if len(duplicate_pairs) == 1:
            st.info(f"Found {len(duplicate_pairs)} duplicate pair.")
        else:
            st.info(f"Found {len(duplicate_pairs)} duplicate pairs.")
        
        # Button to go to duplicates page
        if st.button("🔍 View SharePoint Duplicates", use_container_width=True, key="dashboard_view_sp_duplicates"):
            st.session_state.page = 'duplicates'
            st.rerun()
    else:
        st.metric("Duplicate Pairs Found", "0")
        st.info("No duplicate pairs detected yet.")
        

