"""
Settings page for DocJanitor.
"""
import streamlit as st
from models.database import scan_for_duplicates
from confluence.api import load_documents_from_spaces, get_available_spaces

def render_settings():
    """
    Render the settings page
    """
    st.title("⚙️ Settings")
    st.markdown("Configure DocJanitor settings and perform maintenance operations.")
    
    # Duplicate detection settings
    st.markdown("## 🔍 Duplicate Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.50,
            max_value=0.95,
            value=0.65,
            step=0.05,
            help="Documents with similarity above this threshold will be considered potential duplicates"
        )
    
    with col2:
        st.markdown("**Current Threshold:** 65%")
        st.markdown("- **50-60%:** Very loose matching (many false positives)")
        st.markdown("- **65-75%:** Balanced matching (recommended)")
        st.markdown("- **80-95%:** Strict matching (may miss some duplicates)")
    
    # Manual duplicate scan
    if st.button("🔍 Run Duplicate Scan", use_container_width=True, key="settings_run_scan"):
        with st.spinner("Scanning for duplicates..."):
            result = scan_for_duplicates(similarity_threshold=similarity_threshold, update_existing=True)
            
            if result['success']:
                st.success(f"✅ {result['message']}")
                if result.get('pairs_found', 0) > 0:
                    st.info(f"Found {result['pairs_found']} potential duplicate pairs. Go to the Duplicates page to review them.")
            else:
                st.error(f"❌ Scan failed: {result['message']}")
    
    st.markdown("---")
    
    # Space management
    st.markdown("## 🏢 Space Management")
    
    # Show currently selected spaces
    selected_spaces = st.session_state.get('selected_spaces', [])
    if selected_spaces:
        st.markdown(f"**Currently monitoring {len(selected_spaces)} space(s):** {', '.join(selected_spaces)}")
    else:
        st.warning("No spaces currently selected for monitoring.")
    
    # Load documents from spaces
    st.markdown("### Load Documents from Confluence")
    
    available_spaces = st.session_state.get('available_spaces', [])
    if not available_spaces:
        if st.button("🔄 Load Available Spaces", key="settings_load_spaces"):
            with st.spinner("Loading available spaces..."):
                spaces = get_available_spaces()
                st.session_state.available_spaces = spaces
                st.rerun()
    else:
        space_options = [(space['key'], f"{space['name']} ({space['key']})") for space in available_spaces]
        
        selected_space_keys = st.multiselect(
            "Select spaces to load documents from:",
            options=[key for key, _ in space_options],
            format_func=lambda key: next(label for k, label in space_options if k == key)
        )
        
        col1, col2 = st.columns(2)
        with col1:
            docs_per_space = st.number_input(
                "Documents per space",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                help="Maximum number of documents to load from each space"
            )
        
        with col2:
            if st.button("📥 Load Documents", disabled=not selected_space_keys, key="settings_load_docs"):
                with st.spinner(f"Loading documents from {len(selected_space_keys)} space(s)..."):
                    result = load_documents_from_spaces(selected_space_keys, docs_per_space)
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        # Auto-run duplicate scan after loading
                        if result.get('total_loaded', 0) > 0:
                            st.info("Running automatic duplicate scan on newly loaded documents...")
                            scan_result = scan_for_duplicates(similarity_threshold=similarity_threshold)
                            if scan_result['success'] and scan_result.get('pairs_found', 0) > 0:
                                st.info(f"Found {scan_result['pairs_found']} potential duplicates after loading.")
                    else:
                        st.error(f"❌ {result['message']}")
                        if result.get('errors'):
                            with st.expander("View Errors"):
                                for error in result['errors']:
                                    st.text(error)
    
    st.markdown("---")
    
    # Database maintenance
    st.markdown("## 🗄️ Database Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ChromaDB Status")
        from models.database import get_document_database
        db = get_document_database()
        
        try:
            all_docs = db.get()
            doc_count = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Documents", doc_count)
        except Exception as e:
            st.error(f"Database error: {str(e)}")
    
    with col2:
        st.markdown("### Quick Actions")
        
        if st.button("🧹 Clean Duplicate DB Entries", key="settings_clean_db"):
            from models.database import cleanup_duplicate_database_entries
            with st.spinner("Cleaning up duplicate database entries..."):
                success, message = cleanup_duplicate_database_entries()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
        
        if st.button("🔄 Refresh Space List", key="settings_refresh_spaces"):
            with st.spinner("Refreshing available spaces..."):
                spaces = get_available_spaces()
                st.session_state.available_spaces = spaces
                st.success(f"✅ Loaded {len(spaces)} available spaces")
                st.rerun()
    
    st.markdown("---")
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        st.markdown("### Debug Information")
        
        # Show session state for debugging
        if st.checkbox("Show Session State"):
            st.json({
                "page": st.session_state.get("page"),
                "selected_spaces": st.session_state.get("selected_spaces"),
                "available_spaces_count": len(st.session_state.get("available_spaces", [])),
                "merge_docs": "Set" if st.session_state.get("merge_docs") else "None",
                "merged_content": "Set" if st.session_state.get("merged_content") else "None"
            })
        
        # Reset session state
        if st.button("🔄 Reset Session State", key="settings_reset_session"):
            # Keep only essential state
            essential_keys = ['page', 'selected_spaces', 'available_spaces']
            keys_to_remove = [key for key in st.session_state.keys() if key not in essential_keys]
            
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.success("Session state reset!")
            st.rerun()
    
    # Navigation
    st.markdown("---")
    if st.button("← Back to Dashboard", key="settings_back_to_dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
