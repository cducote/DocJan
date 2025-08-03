"""
Dashboard page for Concatly.
"""
import streamlit as st
import time
from models.database import get_document_database
from sharepoint.api import sharepoint_api

def render_dashboard():
    """
    Render the dashboard page
    """
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
        try:
            all_docs = db.get()
            total_docs = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Confluence Pages", total_docs)
        except Exception as e:
            st.metric("Total Confluence Pages", "Error loading")
    
    with col2:
        st.markdown("## 📋 Detected Duplicates")
        st.markdown("Review and manage Confluence page pairs that have been automatically detected as potential duplicates.")
        
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
    
    with stat_col4:
        # Calculate potential space saved (placeholder)
        st.metric("Potential Merges", len(duplicate_pairs) if 'duplicate_pairs' in locals() else 0)

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
        
        # SharePoint statistics
        try:
            folders = sharepoint_api.get_folders()
            documents = sharepoint_api.get_documents("Concatly_Test_Documents")
            st.metric("SharePoint Folders", len(folders))
            st.metric("Test Documents", len(documents))
        except Exception as e:
            st.metric("SharePoint Folders", "Error loading")
            st.metric("Test Documents", "Error loading")
    
    with col2:
        st.markdown("## 📁 SharePoint Documents")
        st.markdown("View and manage your SharePoint documents.")
        
        # Show recent documents
        try:
            documents = sharepoint_api.get_documents("Concatly_Test_Documents")
            
            if documents:
                st.markdown("### Test Documents:")
                for doc in documents[:5]:  # Show first 5
                    with st.expander(f"📄 {doc['name']}"):
                        st.write(f"**Size:** {doc['size']} bytes")
                        st.write(f"**Modified:** {doc['last_modified']}")
                        if st.button(f"View Content", key=f"view_{doc['id']}"):
                            content = sharepoint_api.get_document_content(doc['id'])
                            if content:
                                st.text_area("Content:", content, height=200)
            else:
                st.info("No test documents found. Run the SharePoint seed script to create some!")
        except Exception as e:
            st.error(f"Error loading SharePoint documents: {e}")
        

