"""
Confluence Spaces management page for Concatly.
"""
import streamlit as st
import pandas as pd
import time
from confluence.api import get_available_spaces, load_documents_from_spaces
from models.database import get_detected_duplicates

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

def render_spaces_page():
    """
    Render the Confluence Spaces management page
    """
    st.title("🌐 Confluence Spaces")
    st.markdown("Select and manage the Confluence spaces to include in document analysis.")
    
    # Load available spaces (cached in session state)
    if st.session_state.available_spaces is None:
        with st.spinner("Loading available spaces..."):
            st.session_state.available_spaces = get_available_spaces()
    
    available_spaces = st.session_state.available_spaces
    
    if not available_spaces:
        st.error("No spaces found or unable to connect to Confluence. Please check your configuration.")
        return
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Select Spaces")
        
        # Create options for multiselect (display names)
        space_options = [space.get('display_name', f"{space['name']} ({space['key']})") for space in available_spaces]
        
        # Find currently selected display names based on selected space keys
        current_selection = []
        for space in available_spaces:
            if space['key'] in st.session_state.selected_spaces:
                current_selection.append(space.get('display_name', f"{space['name']} ({space['key']})"))
        
        # Multiselect for spaces
        selected_display_names = st.multiselect(
            "Choose spaces to include in analysis:",
            options=space_options,
            default=current_selection,
            help="Select one or more spaces to include in duplicate detection and document management.",
            key="spaces_selector"
        )
        
        # Convert display names back to space keys
        selected_keys = []
        for display_name in selected_display_names:
            for space in available_spaces:
                space_display = space.get('display_name', f"{space['name']} ({space['key']})")
                if space_display == display_name:
                    selected_keys.append(space['key'])
                    break
        
        # Update session state
        st.session_state.selected_spaces = selected_keys
        
        # Show selection summary
        if selected_keys:
            st.markdown("### Selected Spaces")
            for key in selected_keys:
                space_info = next((s for s in available_spaces if s['key'] == key), None)
                if space_info:
                    space_type = space_info.get('type', 'unknown')
                    st.markdown(f"- **{space_info['name']}** ({space_info['key']}) - {space_type} space")
        else:
            st.warning("No spaces selected. Please select at least one space to proceed with analysis.")
    
    with col2:
        st.markdown("### Actions")
        
        # Load documents button
        if st.button("📥 Load Documents", use_container_width=True, help="Load documents from selected spaces into database", key="spaces_load_docs"):
            if st.session_state.selected_spaces:
                with st.spinner(f"Loading documents from {len(st.session_state.selected_spaces)} selected spaces..."):
                    load_result = load_documents_from_spaces(st.session_state.selected_spaces)
                    
                    if load_result['success']:
                        st.success(f"✅ {load_result['message']}")
                        # Auto-run duplicate scan
                        if load_result.get('total_loaded', 0) > 0:
                            st.info("Running automatic duplicate scan...")
                            from models.database import scan_for_duplicates
                            scan_result = scan_for_duplicates()
                            if scan_result['success'] and scan_result.get('pairs_found', 0) > 0:
                                st.info(f"Found {scan_result['pairs_found']} potential duplicates.")
                    else:
                        st.error(f"❌ {load_result['message']}")
                        if load_result.get('errors'):
                            with st.expander("View Errors"):
                                for error in load_result['errors']:
                                    st.text(error)
                    
                    # Refresh the page to show updated data
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Please select spaces first before loading documents.")
        
        # Refresh spaces button
        if st.button("🔄 Refresh Spaces", use_container_width=True, key="spaces_refresh"):
            st.session_state.available_spaces = None
            st.rerun()
        
        # Show total available spaces
        st.metric("Available Spaces", len(available_spaces))
        st.metric("Selected Spaces", len(st.session_state.selected_spaces))
        
        # Space types breakdown
        if available_spaces:
            space_types = {}
            for space in available_spaces:
                space_type = space.get('type', 'unknown')
                space_types[space_type] = space_types.get(space_type, 0) + 1
            
            st.markdown("### Space Types")
            for space_type, count in space_types.items():
                st.markdown(f"- {space_type.title()}: {count}")
    
    # Detailed space information
    if available_spaces:
        st.markdown("---")
        st.markdown("### Available Spaces Details")
        
        # Create a dataframe for better display
        spaces_data = []
        for space in available_spaces:
            description = space.get('description', 'No description')
            if len(description) > 100:
                description = description[:100] + "..."
            
            spaces_data.append({
                "Name": space['name'],
                "Key": space['key'],
                "Type": space.get('type', 'unknown').title(),
                "Selected": "✓" if space['key'] in st.session_state.selected_spaces else "",
                "Description": description
            })
        
        df = pd.DataFrame(spaces_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Show detected duplicates for selected spaces
    if st.session_state.selected_spaces:
        st.markdown("---")
        
        # Dynamic title and filter options based on number of spaces selected
        if len(st.session_state.selected_spaces) > 1:
            st.markdown("### 🔍 Detected Duplicates")
            
            # Add filter options when multiple spaces are selected
            col_filter1, col_filter2 = st.columns([2, 1])
            
            with col_filter1:
                duplicate_filter = st.selectbox(
                    "Show duplicates:",
                    options=["All duplicates", "Cross-space only", "Within-space only"],
                    index=0,  # Default to showing all
                    help="Choose which type of duplicates to display",
                    key="spaces_duplicate_filter"
                )
            
            with col_filter2:
                st.markdown("") # Spacer
                st.markdown(f"**{len(st.session_state.selected_spaces)} spaces selected**")
            
            # Determine cross_space_only parameter based on filter
            if duplicate_filter == "Cross-space only":
                cross_space_only = True
                within_space_only = False
                st.markdown("*Showing only duplicates between different spaces*")
            elif duplicate_filter == "Within-space only":
                cross_space_only = False
                within_space_only = True
                st.markdown("*Showing only duplicates within the same space*")
            else:  # "All duplicates"
                cross_space_only = False
                within_space_only = False
                st.markdown("*Showing all duplicates (both cross-space and within-space)*")
        else:
            st.markdown("### 🔍 Detected Duplicates")
            st.markdown("*Showing all duplicates within the selected space*")
            cross_space_only = False
            within_space_only = False
        
        with st.spinner("Loading duplicates for selected spaces..."):
            # Get duplicates filtered by selected spaces and filter type
            duplicate_pairs = get_detected_duplicates(
                space_filter=st.session_state.selected_spaces, 
                cross_space_only=cross_space_only,
                within_space_only=within_space_only
            )
        
        if duplicate_pairs:
            # Show appropriate success message based on filtering
            if len(st.session_state.selected_spaces) > 1:
                if duplicate_filter == "Cross-space only":
                    st.success(f"Found {len(duplicate_pairs)} cross-space duplicate pairs between selected spaces")
                elif duplicate_filter == "Within-space only":
                    st.success(f"Found {len(duplicate_pairs)} within-space duplicate pairs in selected spaces")  
                else:
                    st.success(f"Found {len(duplicate_pairs)} duplicate pairs in selected spaces (cross-space and within-space)")
            else:
                st.success(f"Found {len(duplicate_pairs)} duplicate pairs in selected space")
            
            # Create tabs for different views
            tab1, tab2 = st.tabs(["📋 Summary View", "📊 Detailed View"])
            
            with tab1:
                # Summary cards
                for i, pair in enumerate(duplicate_pairs):
                    with st.container():
                        st.markdown(f"**Duplicate Pair {i+1}**")
                        
                        # Create columns for the two documents
                        col_a, col_b, col_actions = st.columns([3, 3, 2])
                        
                        with col_a:
                            st.markdown(f"📄 **{pair['main_title']}**")
                            st.markdown(f"🌐 Space: **{pair['main_space_name']}**")
                            if pair['main_doc'].metadata.get('source'):
                                st.markdown(f"🔗 [View Page]({pair['main_doc'].metadata['source']})")
                        
                        with col_b:
                            st.markdown(f"📄 **{pair['similar_title']}**")
                            st.markdown(f"🌐 Space: **{pair['similar_space_name']}**")
                            if pair['similar_doc'].metadata.get('source'):
                                st.markdown(f"🔗 [View Page]({pair['similar_doc'].metadata['source']})")
                        
                        with col_actions:
                            # Add similarity meter
                            render_similarity_meter(pair['similarity_score'])
                            
                            # Determine if this is cross-space or within-space
                            if pair['main_space'] != pair['similar_space']:
                                st.markdown("🔄 **Cross-Space**")
                            else:
                                st.markdown("📁 **Within-Space**")
                            
                            # Merge button
                            if st.button(f"🔀 Merge", key=f"spaces_merge_{i}"):
                                st.session_state.merge_docs = {
                                    "main_doc": pair['main_doc'],
                                    "similar_doc": pair['similar_doc'],
                                    "similarity": pair['similarity_score']
                                }
                                st.session_state.page = 'merge'
                                st.rerun()
                        
                        st.markdown("---")
            
            with tab2:
                # Detailed view with full content preview
                for i, pair in enumerate(duplicate_pairs):
                    with st.expander(f"📋 Pair {i+1}: {pair['main_title']} ↔ {pair['similar_title']}"):
                        
                        # Space information
                        col_space1, col_space2 = st.columns(2)
                        with col_space1:
                            st.markdown(f"**Space:** **{pair['main_space_name']}**")
                        with col_space2:
                            st.markdown(f"**Space:** **{pair['similar_space_name']}**")
                        
                        # Content preview
                        col_content1, col_content2 = st.columns(2)
                        
                        with col_content1:
                            st.markdown(f"**{pair['main_title']}**")
                            content_preview = pair['main_doc'].page_content[:300] + "..." if len(pair['main_doc'].page_content) > 300 else pair['main_doc'].page_content
                            st.markdown(f"```\n{content_preview}\n```")
                            if pair['main_doc'].metadata.get('source'):
                                st.markdown(f"🔗 [View Full Page]({pair['main_doc'].metadata['source']})")
                        
                        with col_content2:
                            st.markdown(f"**{pair['similar_title']}**")
                            content_preview = pair['similar_doc'].page_content[:300] + "..." if len(pair['similar_doc'].page_content) > 300 else pair['similar_doc'].page_content
                            st.markdown(f"```\n{content_preview}\n```")
                            if pair['similar_doc'].metadata.get('source'):
                                st.markdown(f"🔗 [View Full Page]({pair['similar_doc'].metadata['source']})")
                        
                        # Action buttons
                        st.markdown("**Actions:**")
                        col_action1, col_action2 = st.columns(2)
                        with col_action1:
                            if st.button(f"🔀 Merge Documents", key=f"spaces_merge_detail_{i}"):
                                st.session_state.merge_docs = {
                                    "main_doc": pair['main_doc'],
                                    "similar_doc": pair['similar_doc'],
                                    "similarity": pair['similarity_score']
                                }
                                st.session_state.page = 'merge'
                                st.rerun()
                        with col_action2:
                            # Add similarity meter in detailed view too
                            render_similarity_meter(pair['similarity_score'])
        else:
            if len(st.session_state.selected_spaces) > 1:
                if duplicate_filter == "Cross-space only":
                    st.info("No cross-space duplicates found between the selected spaces. This could mean:")
                    st.markdown("- No duplicate content exists **between** these spaces")
                    st.markdown("- Documents haven't been analyzed yet")
                    st.markdown("- The similarity threshold may be too high")
                    st.markdown("- Only within-space duplicates exist (try changing the filter)")
                elif duplicate_filter == "Within-space only":
                    st.info("No within-space duplicates found in the selected spaces. This could mean:")
                    st.markdown("- No duplicate content exists **within** each individual space")
                    st.markdown("- Documents haven't been analyzed yet")
                    st.markdown("- The similarity threshold may be too high")
                    st.markdown("- Only cross-space duplicates exist (try changing the filter)")
                else:
                    st.info("No duplicates found in the selected spaces. This could mean:")
                    st.markdown("- No duplicate content exists in these spaces")
                    st.markdown("- Documents haven't been analyzed yet")
                    st.markdown("- The similarity threshold may be too high")
            else:
                st.info("No duplicates found in the selected space. This could mean:")
                st.markdown("- No duplicate content exists in this space")
                st.markdown("- Documents haven't been analyzed yet")
                st.markdown("- The similarity threshold may be too high")
            
            st.markdown("**Try:**")
            st.markdown("- Loading documents using the **📥 Load Documents** button above")
            st.markdown("- Running a duplicate scan from the **⚙️ Settings** page")
            st.markdown("- Checking different spaces or adjusting filters")
