"""
Merge page for DocJanitor.
"""
import streamlit as st
from ai.merging import merge_documents_with_ai
from confluence.api import apply_merge_to_confluence
from utils.helpers import format_timestamp_to_est

def render_merge_page():
    """
    Render the merge page for combining two documents
    """
    st.title("🔀 Document Merge Tool")
    
    # Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = 'duplicates'
            st.rerun()
    
    # Check if we have documents to merge
    if not st.session_state.merge_docs:
        st.warning("No documents selected for merging.")
        return
    
    merge_docs = st.session_state.merge_docs
    main_doc = merge_docs.get("main_doc")
    similar_doc = merge_docs.get("similar_doc")
    similarity = merge_docs.get("similarity", 0)
    
    if not main_doc or not similar_doc:
        st.error("Invalid merge documents data.")
        return
        
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
                merged_result = merge_documents_with_ai(main_doc, similar_doc)
                st.session_state.merged_content = merged_result
                st.success("Documents merged successfully!")
                st.rerun()
    
    with col2:
        if st.button("✏️ Manual Edit", use_container_width=True):
            st.session_state.manual_edit_mode = True
            if not st.session_state.get("merged_content"):
                # Start with the primary document content
                st.session_state.merged_content = main_content
            st.rerun()
    
    with col3:
        if st.button("💾 Save Merged Document", use_container_width=True):
            if st.session_state.get("merged_content"):
                st.success("Merged document saved!")
            else:
                st.warning("No merged content to save. Please merge documents first.")
    
    # Display merged content
    st.markdown("### 📝 Merged Document Preview")
    
    # Check if we're in manual edit mode
    if st.session_state.get("manual_edit_mode", False):
        # Manual edit mode - editable text area
        st.markdown("**Manual Edit Mode** - You can edit the merged content below:")
        edited_content = st.text_area(
            "Edit Merged Content", 
            value=st.session_state.get("merged_content", "Start editing here..."), 
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
        if st.session_state.get("merged_content"):
            st.text_area("Merged Content", st.session_state.merged_content, height=300, disabled=True)
        else:
            st.text_area("Merged Content", "AI-generated merged content will appear here...", height=300, disabled=True)
    
    # Confluence integration section
    if st.session_state.get("merged_content"):
        st.markdown("---")
        st.markdown("### 🔄 Apply to Confluence")
        
        # Debug information
        with st.expander("� Debug Information", expanded=False):
            st.markdown("**Main Document:**")
            st.code(f"Title: {main_doc.metadata.get('title', 'N/A')}")
            st.code(f"Source: {main_doc.metadata.get('source', 'N/A')}")
            
            st.markdown("**Similar Document:**")
            st.code(f"Title: {similar_doc.metadata.get('title', 'N/A')}")
            st.code(f"Source: {similar_doc.metadata.get('source', 'N/A')}")
        
        # Page selection
        st.markdown("**Choose which page to keep:**")
        col_main, col_similar = st.columns(2)
        
        with col_main:
            main_title = main_doc.metadata.get('title', 'Untitled Page')
            if st.button(f"📄 Keep Primary: {main_title}", use_container_width=True, key="keep_main"):
                with st.spinner("Applying merge to Confluence..."):
                    success, message = apply_merge_to_confluence(
                        main_doc, 
                        similar_doc, 
                        st.session_state.merged_content, 
                        keep_main=True
                    )
                    st.session_state.confluence_operation_result = (success, message)
                    st.rerun()
        
        with col_similar:
            similar_title = similar_doc.metadata.get('title', 'Untitled Page')
            if st.button(f"🔗 Keep Similar: {similar_title}", use_container_width=True, key="keep_similar"):
                with st.spinner("Applying merge to Confluence..."):
                    success, message = apply_merge_to_confluence(
                        main_doc, 
                        similar_doc, 
                        st.session_state.merged_content, 
                        keep_main=False
                    )
                    st.session_state.confluence_operation_result = (success, message)
                    st.rerun()
        
        # Show operation result
        if st.session_state.get("confluence_operation_result"):
            success, message = st.session_state.confluence_operation_result
            if success:
                st.success(f"✅ {message}")
                # Clear merge state after successful operation
                st.session_state.merge_docs = None
                st.session_state.merged_content = ""
                st.session_state.manual_edit_mode = False
            else:
                st.error(f"❌ {message}")
            
            # Clear result after showing
            if st.button("🔄 Clear Result", key="clear_result"):
                st.session_state.confluence_operation_result = None
                st.rerun()
        
        # Warning about the operation
        st.warning("⚠️ **Important**: This will permanently update one page and delete the other in Confluence. Make sure you have the necessary permissions and have reviewed the merged content.")
    
    else:
        st.info("� Generate merged content first to enable Confluence integration.")
