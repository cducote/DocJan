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
    st.title("🔀 Merge Documents")
    
    # Check if we have documents to merge
    if not st.session_state.merge_docs:
        st.warning("No documents selected for merging.")
        if st.button("← Back to Duplicates", key="merge_no_docs_back"):
            st.session_state.page = 'duplicates'
            st.rerun()
        return
    
    merge_docs = st.session_state.merge_docs
    main_doc = merge_docs.get("main_doc")
    similar_doc = merge_docs.get("similar_doc")
    similarity = merge_docs.get("similarity", 0)
    
    if not main_doc or not similar_doc:
        st.error("Invalid merge documents data.")
        return
    
    # Display document comparison
    st.markdown(f"### Merging Documents (Similarity: {similarity:.0%})")
    
    col1, col2 = st.columns(2)
    
    # Document 1
    with col1:
        with st.container(border=True):
            st.markdown("#### Document A (Primary)")
            title1 = main_doc.metadata.get("title", "Untitled")
            url1 = main_doc.metadata.get("source", "")
            if url1:
                st.markdown(f"**Title:** [{title1}]({url1})")
            else:
                st.markdown(f"**Title:** {title1}")
            
            # Metadata
            space1 = main_doc.metadata.get("space_key", "Unknown")
            space_name1 = main_doc.metadata.get("space_name", space1)
            st.markdown(f"**Space:** {space_name1}")
            
            updated1 = main_doc.metadata.get("last_updated", "")
            if updated1:
                st.markdown(f"**Updated:** {format_timestamp_to_est(updated1)}")
            
            # Content preview
            with st.expander("View Full Content", expanded=False):
                st.markdown(main_doc.page_content)
    
    # Document 2
    with col2:
        with st.container(border=True):
            st.markdown("#### Document B (Similar)")
            title2 = similar_doc.metadata.get("title", "Untitled")
            url2 = similar_doc.metadata.get("source", "")
            if url2:
                st.markdown(f"**Title:** [{title2}]({url2})")
            else:
                st.markdown(f"**Title:** {title2}")
            
            # Metadata
            space2 = similar_doc.metadata.get("space_key", "Unknown")
            space_name2 = similar_doc.metadata.get("space_name", space2)
            st.markdown(f"**Space:** {space_name2}")
            
            updated2 = similar_doc.metadata.get("last_updated", "")
            if updated2:
                st.markdown(f"**Updated:** {format_timestamp_to_est(updated2)}")
            
            # Content preview
            with st.expander("View Full Content", expanded=False):
                st.markdown(similar_doc.page_content)
    
    # Merge options
    st.markdown("---")
    st.markdown("### Merge Options")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Which document should be kept?**")
        keep_main = st.radio(
            "Keep document",
            options=[True, False],
            format_func=lambda x: f"Document A: {title1}" if x else f"Document B: {title2}",
            key="keep_main_doc"
        )
    
    with col2:
        st.markdown("**Merge method**")
        merge_method = st.radio(
            "Method",
            options=["ai", "manual"],
            format_func=lambda x: "AI-assisted merge" if x == "ai" else "Manual editing",
            key="merge_method"
        )
    
    # Generate merged content
    if merge_method == "ai":
        if st.button("🤖 Generate AI Merge", use_container_width=True, key="merge_generate_ai"):
            with st.spinner("Generating merged content using AI..."):
                merged_content = merge_documents_with_ai(main_doc, similar_doc)
                st.session_state.merged_content = merged_content
                st.session_state.manual_edit_mode = False
    
    # Manual editing option
    if merge_method == "manual" or st.session_state.get("manual_edit_mode", False):
        st.markdown("### Manual Content Editing")
        if st.button("✏️ Enable Manual Editing", key="merge_enable_manual"):
            st.session_state.manual_edit_mode = True
            # Start with content from the document we're keeping
            if keep_main:
                st.session_state.merged_content = main_doc.page_content
            else:
                st.session_state.merged_content = similar_doc.page_content
    
    # Display and edit merged content
    if st.session_state.get("merged_content"):
        st.markdown("### Merged Content")
        
        if st.session_state.get("manual_edit_mode", False):
            # Editable version
            edited_content = st.text_area(
                "Edit the merged content:",
                value=st.session_state.merged_content,
                height=400,
                key="content_editor"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", key="merge_save_changes"):
                    st.session_state.merged_content = edited_content
                    st.success("Changes saved!")
            
            with col2:
                if st.button("👁️ Preview Mode", key="merge_preview_mode"):
                    st.session_state.manual_edit_mode = False
                    st.rerun()
        else:
            # Preview version
            with st.container(border=True):
                st.markdown(st.session_state.merged_content)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit Content", key="merge_edit_content"):
                    st.session_state.manual_edit_mode = True
                    st.rerun()
            
            with col2:
                if st.button("🔄 Regenerate with AI", key="merge_regenerate_ai"):
                    with st.spinner("Regenerating merged content..."):
                        merged_content = merge_documents_with_ai(main_doc, similar_doc)
                        st.session_state.merged_content = merged_content
                        st.rerun()
    
    # Apply merge actions
    if st.session_state.get("merged_content"):
        st.markdown("---")
        st.markdown("### Apply Merge")
        
        st.warning("⚠️ **Warning:** This action will update one document and delete the other in Confluence. This operation can be undone from the Merge History page.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("❌ Cancel", use_container_width=True, key="merge_cancel"):
                st.session_state.merge_docs = None
                st.session_state.merged_content = ""
                st.session_state.manual_edit_mode = False
                st.session_state.page = 'duplicates'
                st.rerun()
        
        with col2:
            if st.button("📝 Save Draft", use_container_width=True, key="merge_save_draft"):
                st.success("Draft saved! You can return to continue editing later.")
        
        with col3:
            if st.button("✅ Apply Merge", use_container_width=True, type="primary", key="merge_apply"):
                with st.spinner("Applying merge to Confluence..."):
                    success, message = apply_merge_to_confluence(
                        main_doc, 
                        similar_doc, 
                        st.session_state.merged_content, 
                        keep_main
                    )
                    
                    if success:
                        st.success(message)
                        st.session_state.confluence_operation_result = {
                            "success": True,
                            "message": message
                        }
                        # Clear merge state
                        st.session_state.merge_docs = None
                        st.session_state.merged_content = ""
                        st.session_state.manual_edit_mode = False
                        # Navigate to merge history
                        st.session_state.page = 'merge_history'
                        st.rerun()
                    else:
                        st.error(f"Failed to apply merge: {message}")
                        st.session_state.confluence_operation_result = {
                            "success": False,
                            "message": message
                        }
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Duplicates", key="merge_back_to_duplicates"):
            st.session_state.page = 'duplicates'
            st.rerun()
    
    with col2:
        if st.button("📜 View Merge History", key="merge_view_history"):
            st.session_state.page = 'merge_history'
            st.rerun()
