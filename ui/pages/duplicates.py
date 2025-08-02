"""
Duplicates page for Concatly.
"""
import streamlit as st
from utils.helpers import get_detected_duplicates, format_timestamp_to_est

def render_similarity_meter(similarity_score):
    """Render a visual similarity meter"""
    similarity_pct = int(similarity_score * 100)
    
    # Determine color based on similarity level
    if similarity_pct >= 90:
        color = "#ff4444"  # High similarity - red
        level = "Very High"
    elif similarity_pct >= 80:
        color = "#ff8800"  # High similarity - orange
        level = "High"
    elif similarity_pct >= 70:
        color = "#ffaa00"  # Medium-high similarity - yellow-orange
        level = "Medium-High"
    elif similarity_pct >= 60:
        color = "#ffdd00"  # Medium similarity - yellow
        level = "Medium"
    else:
        color = "#88cc00"  # Lower similarity - green
        level = "Low-Medium"
    
    # Create the meter HTML
    meter_html = f"""
    <div style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 12px; font-weight: 500; color: #666;">Similarity</span>
            <span style="font-size: 12px; font-weight: 600; color: {color};">{similarity_pct}%</span>
        </div>
        <div style="width: 100%; height: 8px; background-color: #e0e0e0; border-radius: 4px; overflow: hidden;">
            <div style="width: {similarity_pct}%; height: 100%; background-color: {color}; transition: width 0.3s ease;"></div>
        </div>
        <div style="text-align: center; margin-top: 2px;">
            <span style="font-size: 10px; color: #888; font-weight: 500;">{level}</span>
        </div>
    </div>
    """
    
    st.markdown(meter_html, unsafe_allow_html=True)

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

    # Create tabs for different views
    tab1, tab2 = st.tabs(["📋 Summary View", "📖 Detailed View"])
    
    with tab1:
        # Summary view - compact list
        st.markdown(f"### Found {len(filtered_pairs)} duplicate pairs")
        
        for i, pair in enumerate(filtered_pairs):
            doc1 = pair.get("doc1", {})
            doc2 = pair.get("doc2", {})
            similarity = pair.get("similarity", 0)
            
            with st.container(border=True):
                # Create columns for the two documents and actions
                col_a, col_b, col_actions = st.columns([3, 3, 2])
                
                with col_a:
                    title1 = doc1.metadata.get("title", "Untitled")
                    space1 = doc1.metadata.get("space_key", "Unknown")
                    space_name1 = doc1.metadata.get("space_name", space1)
                    
                    st.markdown(f"📄 **{title1}**")
                    st.markdown(f"🌐 Space: **{space_name1}**")
                    if doc1.metadata.get('source'):
                        st.markdown(f"🔗 [View Page]({doc1.metadata['source']})")
                
                with col_b:
                    title2 = doc2.metadata.get("title", "Untitled")
                    space2 = doc2.metadata.get("space_key", "Unknown")
                    space_name2 = doc2.metadata.get("space_name", space2)
                    
                    st.markdown(f"📄 **{title2}**")
                    st.markdown(f"🌐 Space: **{space_name2}**")
                    if doc2.metadata.get('source'):
                        st.markdown(f"🔗 [View Page]({doc2.metadata['source']})")
                
                with col_actions:
                    # Add similarity meter
                    render_similarity_meter(similarity)
                    
                    # Determine if this is cross-space or within-space
                    if space1 != space2:
                        st.markdown("🔄 **Cross-Space**")
                    else:
                        st.markdown("📁 **Within-Space**")
                    
                    # Merge button
                    if st.button(f"🔀 Merge", key=f"dup_merge_{i}"):
                        st.session_state.merge_docs = {
                            "main_doc": doc1,
                            "similar_doc": doc2,
                            "similarity": similarity
                        }
                        st.session_state.page = 'merge'
                        st.rerun()
                
                st.markdown("---")
    
    with tab2:
        # Detailed view with full content preview
        for i, pair in enumerate(filtered_pairs):
            doc1 = pair.get("doc1", {})
            doc2 = pair.get("doc2", {})
            similarity = pair.get("similarity", 0)
            
            title1 = doc1.metadata.get("title", "Untitled")
            title2 = doc2.metadata.get("title", "Untitled")
            
            with st.expander(f"📋 Pair {i+1}: {title1} ↔ {title2}"):
                
                # Space information
                col_space1, col_space2 = st.columns(2)
                with col_space1:
                    space1 = doc1.metadata.get("space_key", "Unknown")
                    space_name1 = doc1.metadata.get("space_name", space1)
                    st.markdown(f"**Space:** **{space_name1}**")
                with col_space2:
                    space2 = doc2.metadata.get("space_key", "Unknown")
                    space_name2 = doc2.metadata.get("space_name", space2)
                    st.markdown(f"**Space:** **{space_name2}**")
                
                # Content preview
                col_content1, col_content2 = st.columns(2)
                
                with col_content1:
                    st.markdown(f"**{title1}**")
                    content_preview = doc1.page_content[:300] + "..." if len(doc1.page_content) > 300 else doc1.page_content
                    st.markdown(f"```\n{content_preview}\n```")
                    if doc1.metadata.get('source'):
                        st.markdown(f"🔗 [View Full Page]({doc1.metadata['source']})")
                    
                    # Updated timestamp
                    updated1 = doc1.metadata.get("last_updated", "")
                    if updated1:
                        st.markdown(f"**Updated:** {format_timestamp_to_est(updated1)}")
                
                with col_content2:
                    st.markdown(f"**{title2}**")
                    content_preview = doc2.page_content[:300] + "..." if len(doc2.page_content) > 300 else doc2.page_content
                    st.markdown(f"```\n{content_preview}\n```")
                    if doc2.metadata.get('source'):
                        st.markdown(f"🔗 [View Full Page]({doc2.metadata['source']})")
                    
                    # Updated timestamp
                    updated2 = doc2.metadata.get("last_updated", "")
                    if updated2:
                        st.markdown(f"**Updated:** {format_timestamp_to_est(updated2)}")
                
                # Action buttons
                st.markdown("**Actions:**")
                col_action1, col_action2 = st.columns(2)
                with col_action1:
                    if st.button(f"🔀 Merge Documents", key=f"dup_merge_detail_{i}"):
                        st.session_state.merge_docs = {
                            "main_doc": doc1,
                            "similar_doc": doc2,
                            "similarity": similarity
                        }
                        st.session_state.page = 'merge'
                        st.rerun()
                with col_action2:
                    # Add similarity meter in detailed view too
                    render_similarity_meter(similarity)
