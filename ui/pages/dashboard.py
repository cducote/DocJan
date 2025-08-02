"""
Dashboard page for Concatly.
"""
import streamlit as st
import time
from models.database import get_document_database

def render_dashboard():
    """
    Render the dashboard page
    """
    st.title("🏠 Dashboard")
    st.markdown("Welcome to Concatly - your Confluence duplicate document manager!")
    
    # Get database
    db = get_document_database()
    
    # Create two columns for the main sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 🔍 Search")
        st.markdown("Search for documents and discover potential duplicates using semantic search.")
        
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
        from utils.helpers import get_detected_duplicates
        duplicate_pairs = get_detected_duplicates()  # No space filter for dashboard - show all
        
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
            all_docs = db.get()
            total_docs = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Documents", total_docs)
        except:
            st.metric("Total Documents", "Error")
    
    with stat_col2:
        st.metric("Duplicate Pairs", len(duplicate_pairs) if 'duplicate_pairs' in locals() else 0)
    
    with stat_col3:
        # Calculate documents involved in duplicates
        docs_with_duplicates = len(duplicate_pairs) * 2 if 'duplicate_pairs' in locals() else 0  # Each pair involves 2 docs
        st.metric("Documents with Duplicates", docs_with_duplicates)
    
    # Maintenance section
    st.markdown("---")
    st.markdown("## 🔧 Maintenance")
    
    maint_col1, maint_col2 = st.columns(2)
    
    with maint_col1:
        st.markdown("### 🔍 Duplicate Detection")
        st.markdown("Manually scan all documents to find new duplicate pairs. This is useful after undoing merges or when new content is added.")
        
        if st.button("🔄 Scan for Duplicates", use_container_width=True, key="dashboard_scan_duplicates", help="Re-scan all documents for duplicate pairs"):
            with st.spinner("Scanning documents for duplicates..."):
                from models.database import scan_for_duplicates
                scan_result = scan_for_duplicates(similarity_threshold=0.65, update_existing=True)
                
                if scan_result['success']:
                    if scan_result['pairs_found'] > 0:
                        st.success(f"✅ Scan completed! Found {scan_result['pairs_found']} duplicate pairs and updated {scan_result['documents_updated']} documents.")
                        # Refresh the page to show new duplicates
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info("✅ Scan completed. No duplicate pairs found.")
                else:
                    st.error(f"❌ Scan failed: {scan_result['message']}")
    
    with maint_col2:
        st.markdown("### ⚙️ Advanced Settings")
        st.markdown("Advanced maintenance and configuration options.")
        
        # Show last scan info if available
        try:
            all_docs = db.get()
            if all_docs['metadatas']:
                last_scan_times = []
                for metadata in all_docs['metadatas']:
                    last_scan = metadata.get('last_similarity_scan')
                    if last_scan:
                        last_scan_times.append(last_scan)
                
                if last_scan_times:
                    # Get the most recent scan time
                    most_recent_scan = max(last_scan_times)
                    from utils.helpers import format_timestamp_to_est
                    formatted_time = format_timestamp_to_est(most_recent_scan)
                    st.info(f"Last duplicate scan: {formatted_time}")
                else:
                    st.info("No previous duplicate scans found")
        except Exception as e:
            st.info("Could not retrieve scan history")
    
    with stat_col4:
        # Calculate potential space saved (placeholder)
        st.metric("Potential Merges", len(duplicate_pairs) if 'duplicate_pairs' in locals() else 0)
