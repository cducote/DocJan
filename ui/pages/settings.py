"""
Settings page for Concatly.
"""
import streamlit as st
from models.database import scan_for_duplicates
from confluence.api import load_documents_from_spaces, get_available_spaces

def render_settings():
    """
    Render the settings page
    """
    st.title("⚙️ Settings")
    st.markdown("Configure Concatly settings and perform maintenance operations.")
    
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
    
    # Essential maintenance only
    st.markdown("## 🔧 Basic Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Database Status")
        from models.database import get_document_database
        db = get_document_database()
        
        try:
            all_docs = db.get()
            doc_count = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Documents", doc_count)
            
            # Show warning if document count seems too high
            if doc_count > 15:  # Assuming you should have around 10 docs
                st.warning(f"⚠️ Document count seems high ({doc_count}). You may have duplicates in ChromaDB.")
        except Exception as e:
            st.error(f"Database error: {str(e)}")
    
    with col2:
        st.markdown("### Space Management")
        
        if st.button("🔄 Refresh Space List", key="settings_refresh_spaces"):
            with st.spinner("Refreshing available spaces..."):
                spaces = get_available_spaces()
                st.session_state.available_spaces = spaces
                st.success(f"✅ Loaded {len(spaces)} available spaces")
                st.rerun()
    
    # Database maintenance section
    st.markdown("### 🗃️ Database Maintenance")
    st.markdown("Use these tools to fix common database issues:")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("🧹 Clear ChromaDB", key="settings_clear_chromadb", type="secondary"):
            st.warning("⚠️ This will clear all document embeddings from ChromaDB. You'll need to reload your documents after this.")
            
            if st.button("✅ Confirm Clear ChromaDB", key="settings_confirm_clear"):
                with st.spinner("Clearing ChromaDB..."):
                    try:
                        # Import the reset function from reset.py
                        import sys
                        import os
                        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                        from reset import reset_chroma_database
                        
                        success, message = reset_chroma_database()
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info("💡 Now reload your documents from the Space Management section above.")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Error clearing ChromaDB: {str(e)}")
                    
                    # Force a rerun to update the document count
                    st.rerun()
    
    with col4:
        st.markdown("**When to use Clear ChromaDB:**")
        st.markdown("- Document count is much higher than expected")
        st.markdown("- Seeing duplicate documents in search results")
        st.markdown("- False duplicate detection results")
        st.markdown("- After multiple scans without clearing first")
    
    st.markdown("---")
    
    # Simple debug info
    with st.expander("🔍 Debug Information"):
        st.markdown("### Session Info")
        
        # Safely handle potentially None values
        available_spaces = st.session_state.get("available_spaces", [])
        available_spaces_count = len(available_spaces) if available_spaces is not None else 0
        
        selected_spaces = st.session_state.get("selected_spaces", [])
        selected_spaces_safe = selected_spaces if selected_spaces is not None else []
        
        st.json({
            "page": st.session_state.get("page"),
            "platform": st.session_state.get("platform"),
            "selected_spaces": selected_spaces_safe,
            "available_spaces_count": available_spaces_count
        })
    
    # Navigation
    st.markdown("---")
    if st.button("← Back to Dashboard", key="settings_back_to_dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
