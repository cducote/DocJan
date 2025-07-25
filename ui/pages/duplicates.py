"""
Duplicates page for DocJanitor.
"""
import streamlit as st
from utils.helpers import get_detected_duplicates, format_timestamp_to_est

def render_duplicates_page():
    """
    Render the duplicates page
    """
    st.title("🔄 Duplicate Detection")
    st.markdown("Review and manage document pairs that have been automatically detected as potential duplicates.")
    
    # Get detected duplicates
    duplicate_pairs = get_detected_duplicates(space_keys=st.session_state.selected_spaces)
    
    # Show filters
    col1, col2 = st.columns([1, 3])
    with col1:
        min_similarity = st.slider(
            "Min. Similarity", 
            min_value=0.50, 
            max_value=1.0, 
            value=0.65,
            step=0.01, 
            format="%.2f"
        )
    
    with col2:
        st.info(f"Showing {len(duplicate_pairs)} potential duplicate pairs with similarity >= {min_similarity:.0%}")
    
    # Filter pairs by similarity
    filtered_pairs = [pair for pair in duplicate_pairs if pair.get("similarity", 0) >= min_similarity]
    
    if not filtered_pairs:
        st.info("No duplicate pairs found with the current filters.")
        return
    
    # Display duplicate pairs
    for i, pair in enumerate(filtered_pairs):
        doc1 = pair.get("doc1", {})
        doc2 = pair.get("doc2", {})
        similarity = pair.get("similarity", 0)
        
        # Card for duplicate pair
        with st.container(border=True):
            # Header with similarity score
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### Potential Duplicate #{i+1}")
            
            with col2:
                st.metric("Similarity", f"{similarity:.0%}")
            
            # Documents side by side
            col1, col2 = st.columns(2)
            
            # Document 1
            with col1:
                with st.container(border=True):
                    title1 = doc1.metadata.get("title", "Untitled")
                    url1 = doc1.metadata.get("source", "")
                    if url1:
                        st.markdown(f"#### [Document 1: {title1}]({url1})")
                    else:
                        st.markdown(f"#### Document 1: {title1}")
                    
                    # Metadata
                    col_a, col_b = st.columns(2)
                    with col_a:
                        space = doc1.metadata.get("space_key", "Unknown")
                        space_name = doc1.metadata.get("space_name", space)
                        st.markdown(f"**Space:** {space_name}")
                    
                    with col_b:
                        updated = doc1.metadata.get("last_updated", "")
                        if updated:
                            st.markdown(f"**Updated:** {format_timestamp_to_est(updated)}")
                    
                    # Content preview
                    with st.expander("Preview Content"):
                        st.markdown(doc1.page_content[:300] + "..." if len(doc1.page_content) > 300 else doc1.page_content)
            
            # Document 2
            with col2:
                with st.container(border=True):
                    title2 = doc2.metadata.get("title", "Untitled")
                    url2 = doc2.metadata.get("source", "")
                    if url2:
                        st.markdown(f"#### [Document 2: {title2}]({url2})")
                    else:
                        st.markdown(f"#### Document 2: {title2}")
                    
                    # Metadata
                    col_a, col_b = st.columns(2)
                    with col_a:
                        space = doc2.metadata.get("space_key", "Unknown")
                        space_name = doc2.metadata.get("space_name", space)
                        st.markdown(f"**Space:** {space_name}")
                    
                    with col_b:
                        updated = doc2.metadata.get("last_updated", "")
                        if updated:
                            st.markdown(f"**Updated:** {format_timestamp_to_est(updated)}")
                    
                    # Content preview
                    with st.expander("Preview Content"):
                        st.markdown(doc2.page_content[:300] + "..." if len(doc2.page_content) > 300 else doc2.page_content)
            
            # Actions
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("View Detailed Comparison", key=f"compare_{i}"):
                    st.session_state.selected_pair = pair
                    st.session_state.page = 'compare'
                    st.rerun()
            
            with col2:
                if st.button("Merge Documents", key=f"merge_{i}"):
                    st.session_state.merge_docs = {
                        "main_doc": doc1,
                        "similar_doc": doc2,
                        "similarity": similarity
                    }
                    st.session_state.page = 'merge'
                    st.rerun()
