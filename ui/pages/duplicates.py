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
    
    # Check current platform
    platform = st.session_state.get('platform', 'confluence')
    
    if platform == 'confluence':
        st.markdown("Review and manage Confluence document pairs that have been automatically detected as potential duplicates.")
        render_confluence_duplicates()
    else:
        st.markdown("Review and manage SharePoint document pairs that have been automatically detected as potential duplicates.")
        render_sharepoint_duplicates()

def render_confluence_duplicates():
    """Render Confluence-specific duplicates"""
    # Show loading spinner
    with st.spinner("Loading Confluence duplicates..."):
        # Add basic caching for Confluence duplicates too
        confluence_cache_key = f"confluence_duplicates_{'-'.join(st.session_state.get('selected_spaces', ['SD']))}"
        
        if confluence_cache_key not in st.session_state:
            # Get detected duplicates
            duplicate_pairs = get_detected_duplicates(space_keys=st.session_state.selected_spaces)
            st.session_state[confluence_cache_key] = duplicate_pairs
        else:
            duplicate_pairs = st.session_state[confluence_cache_key]
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Found {len(duplicate_pairs)} potential duplicate pairs.")
    with col2:
        if st.button("🔄 Refresh", key="refresh_confluence"):
            # Clear cache when refresh is clicked
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith("confluence_duplicates_")]
            for key in keys_to_remove:
                del st.session_state[key]
            st.rerun()
    
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

    render_duplicate_pairs(filtered_pairs, platform="confluence")

def load_sharepoint_duplicates():
    """Load SharePoint documents and calculate duplicates (with error handling)"""
    try:
        from sharepoint.api import SharePointAPI
        sharepoint_api = SharePointAPI()
        
        # Get SharePoint documents
        documents = sharepoint_api.get_documents("Concatly_Test_Documents")
        
        if not documents:
            return {
                "documents": [],
                "duplicate_pairs": [],
                "error": None
            }
        
        # Enhanced duplicate detection based on document names and content patterns
        duplicate_pairs = []
        
        # Optimized similarity detection - only process if we have enough documents
        if len(documents) >= 2:
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    similarity_score = calculate_sharepoint_similarity(doc1, doc2)
                    
                    # Only add pairs above threshold to reduce processing
                    if similarity_score > 0.2:  # Lower threshold to catch more potential duplicates
                        duplicate_pairs.append({
                            "doc1": {
                                "metadata": {
                                    "title": doc1['name'], 
                                    "source": doc1.get('webUrl', '#'), 
                                    "platform": "sharepoint"
                                }, 
                                "id": doc1['id']
                            },
                            "doc2": {
                                "metadata": {
                                    "title": doc2['name'], 
                                    "source": doc2.get('webUrl', '#'), 
                                    "platform": "sharepoint"
                                }, 
                                "id": doc2['id']
                            },
                            "similarity": similarity_score
                        })
        
        return {
            "documents": documents,
            "duplicate_pairs": duplicate_pairs,
            "error": None
        }
        
    except Exception as e:
        return {
            "documents": [],
            "duplicate_pairs": [],
            "error": str(e)
        }

def render_sharepoint_duplicates():
    """Render SharePoint-specific duplicates"""
    # Use session state for caching
    cache_key = "sharepoint_duplicates_cache"
    
    # Check if we have cached data
    if cache_key not in st.session_state:
        with st.spinner("Loading SharePoint documents and analyzing duplicates..."):
            st.session_state[cache_key] = load_sharepoint_duplicates()
    
    # Get cached data
    cached_data = st.session_state[cache_key]
    
    if cached_data["error"]:
        st.error(f"Error loading SharePoint duplicates: {cached_data['error']}")
        st.info("Make sure SharePoint is properly configured and accessible.")
        # Add refresh button
        if st.button("🔄 Retry", key="retry_sharepoint"):
            del st.session_state[cache_key]
            st.rerun()
        return
    
    documents = cached_data["documents"]
    duplicate_pairs = cached_data["duplicate_pairs"]
    
    if not documents:
        st.info("No SharePoint documents found. Upload some documents to see duplicates.")
        if st.button("🔄 Refresh", key="refresh_sharepoint"):
            del st.session_state[cache_key]
            st.rerun()
        return
    
    # Add refresh button for manual cache clearing
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Found {len(documents)} SharePoint documents. Analyzed {len(duplicate_pairs)} potential duplicate pairs.")
    with col2:
        if st.button("🔄 Refresh Data", key="refresh_sp_data"):
            del st.session_state[cache_key]
            st.rerun()
        
        # Show filters
        col1, col2 = st.columns([1, 3])
        with col1:
            min_similarity = st.slider(
                "Min. Similarity", 
                min_value=0.20, 
                max_value=1.0, 
                value=0.40,
                step=0.01, 
                format="%.2f",
                key="sp_similarity"
            )
        
        with col2:
            st.info(f"Showing duplicate pairs with similarity >= {min_similarity:.0%}")
        
        # Filter pairs by similarity
        filtered_pairs = [pair for pair in duplicate_pairs if pair.get("similarity", 0) >= min_similarity]
        
        if not filtered_pairs:
            st.warning("No duplicate pairs found with the current filters. Try lowering the similarity threshold.")
            
            # Show debug information
            with st.expander("🔍 Debug Information"):
                st.markdown("**All Documents Found:**")
                for i, doc in enumerate(documents):
                    st.write(f"{i+1}. {doc['name']}")
                
                if duplicate_pairs:
                    st.markdown(f"**All {len(duplicate_pairs)} Potential Pairs (before filtering):**")
                    for i, pair in enumerate(duplicate_pairs):
                        doc1_name = pair["doc1"]["metadata"]["title"]
                        doc2_name = pair["doc2"]["metadata"]["title"]
                        similarity = pair["similarity"]
                        st.write(f"{i+1}. {doc1_name} ↔ {doc2_name} ({similarity:.2%})")
            return

        render_duplicate_pairs(filtered_pairs, platform="sharepoint")

def calculate_sharepoint_similarity(doc1, doc2):
    """Calculate similarity between two SharePoint documents"""
    name1 = doc1['name'].lower()
    name2 = doc2['name'].lower()
    
    # Remove file extensions
    name1_clean = name1.replace('.txt', '').replace('.docx', '').replace('.pdf', '')
    name2_clean = name2.replace('.txt', '').replace('.docx', '').replace('.pdf', '')
    
    # Multiple similarity checks
    similarities = []
    
    # 1. Direct name similarity (for files like "v1" vs "v2")
    if name1_clean.replace('v1', '').replace('v2', '').replace('_', ' ').replace('-', ' ') == \
       name2_clean.replace('v1', '').replace('v2', '').replace('_', ' ').replace('-', ' '):
        similarities.append(0.9)  # Very high similarity for version differences
    
    # 2. Word-based similarity
    words1 = set(name1_clean.replace('_', ' ').replace('-', ' ').split())
    words2 = set(name2_clean.replace('_', ' ').replace('-', ' ').split())
    
    # Remove version numbers and common words
    common_stopwords = {'v1', 'v2', 'guide', 'how', 'to', 'the', 'and', 'or', 'for', 'of'}
    words1 = words1 - common_stopwords
    words2 = words2 - common_stopwords
    
    if len(words1) > 0 and len(words2) > 0:
        common_words = words1.intersection(words2)
        word_similarity = len(common_words) / len(words1.union(words2))
        similarities.append(word_similarity)
    
    # 3. Substring similarity for similar concepts
    similarity_patterns = [
        ('password', 'reset'),
        ('meeting', 'guidelines'),
        ('best', 'practices'),
        ('security', 'policy'),
        ('remote', 'work')
    ]
    
    for pattern in similarity_patterns:
        if all(word in name1_clean for word in pattern) and all(word in name2_clean for word in pattern):
            similarities.append(0.8)
    
    # Return the highest similarity score
    return max(similarities) if similarities else 0.0

def render_duplicate_pairs(filtered_pairs, platform="confluence"):
    """Render duplicate pairs for any platform"""
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
                    # Handle Document objects vs dictionaries
                    if hasattr(doc1, 'metadata'):
                        # It's a Document object
                        title1 = doc1.metadata.get("title", "Untitled") if doc1.metadata else "Untitled"
                        space1 = doc1.metadata.get("space_key", "Unknown") if doc1.metadata else "Unknown"
                        space_name1 = doc1.metadata.get("space_name", space1) if doc1.metadata else space1
                        source1 = doc1.metadata.get("source") if doc1.metadata else None
                    else:
                        # It's a dictionary
                        title1 = doc1.get("metadata", {}).get("title", "Untitled")
                        space1 = doc1.get("metadata", {}).get("space_key", "Unknown")
                        space_name1 = doc1.get("metadata", {}).get("space_name", space1)
                        source1 = doc1.get("metadata", {}).get('source')
                    
                    st.markdown(f"📄 **{title1}**")
                    
                    if platform == "confluence":
                        st.markdown(f"🌐 Space: **{space_name1}**")
                    else:
                        st.markdown(f"📁 **SharePoint Document**")
                    
                    if source1:
                        st.markdown(f"🔗 [View Document]({source1})")

                with col_b:
                    # Handle Document objects vs dictionaries
                    if hasattr(doc2, 'metadata'):
                        # It's a Document object
                        title2 = doc2.metadata.get("title", "Untitled") if doc2.metadata else "Untitled"
                        space2 = doc2.metadata.get("space_key", "Unknown") if doc2.metadata else "Unknown"
                        space_name2 = doc2.metadata.get("space_name", space2) if doc2.metadata else space2
                        source2 = doc2.metadata.get("source") if doc2.metadata else None
                    else:
                        # It's a dictionary
                        title2 = doc2.get("metadata", {}).get("title", "Untitled")
                        space2 = doc2.get("metadata", {}).get("space_key", "Unknown")
                        space_name2 = doc2.get("metadata", {}).get("space_name", space2)
                        source2 = doc2.get("metadata", {}).get('source')
                    
                    st.markdown(f"📄 **{title2}**")
                    
                    if platform == "confluence":
                        st.markdown(f"🌐 Space: **{space_name2}**")
                    else:
                        st.markdown(f"📁 **SharePoint Document**")
                    
                    if source2:
                        st.markdown(f"🔗 [View Document]({source2})")

                with col_actions:
                    # Add similarity meter
                    render_similarity_meter(similarity)

                    if platform == "confluence":
                        # Determine if this is cross-space or within-space
                        if hasattr(doc1, 'metadata') and hasattr(doc2, 'metadata'):
                            # Document objects
                            space1 = doc1.metadata.get("space_key", "Unknown") if doc1.metadata else "Unknown"
                            space2 = doc2.metadata.get("space_key", "Unknown") if doc2.metadata else "Unknown"
                        else:
                            # Dictionary objects
                            space1 = doc1.get("metadata", {}).get("space_key", "Unknown")
                            space2 = doc2.get("metadata", {}).get("space_key", "Unknown")
                        
                        if space1 != space2:
                            st.markdown("🔄 **Cross-Space**")
                        else:
                            st.markdown("📁 **Within-Space**")
                    else:
                        st.markdown("📁 **SharePoint**")
                    
                    # Merge button - only for Confluence for now
                    if platform == "confluence":
                        if st.button(f"🔀 Merge", key=f"dup_merge_{i}"):
                            st.session_state.merge_docs = {
                                "main_doc": doc1,
                                "similar_doc": doc2,
                                "similarity": similarity
                            }
                            st.session_state.page = 'merge'
                            st.rerun()
                    else:
                        st.info("SharePoint merge coming soon!")
                
                st.markdown("---")
    
    with tab2:
        # Detailed view with content preview
        for i, pair in enumerate(filtered_pairs):
            doc1 = pair.get("doc1", {})
            doc2 = pair.get("doc2", {})
            similarity = pair.get("similarity", 0)
            
            # Handle Document objects vs dictionaries for titles
            if hasattr(doc1, 'metadata'):
                title1 = doc1.metadata.get("title", "Untitled") if doc1.metadata else "Untitled"
            else:
                title1 = doc1.get("metadata", {}).get("title", "Untitled")
                
            if hasattr(doc2, 'metadata'):
                title2 = doc2.metadata.get("title", "Untitled") if doc2.metadata else "Untitled"
            else:
                title2 = doc2.get("metadata", {}).get("title", "Untitled")
            
            with st.expander(f"📋 Pair {i+1}: {title1} ↔ {title2}"):
                
                # Platform-specific information
                if platform == "confluence":
                    # Space information
                    col_space1, col_space2 = st.columns(2)
                    with col_space1:
                        if hasattr(doc1, 'metadata'):
                            space1 = doc1.metadata.get("space_key", "Unknown") if doc1.metadata else "Unknown"
                            space_name1 = doc1.metadata.get("space_name", space1) if doc1.metadata else space1
                        else:
                            space1 = doc1.get("metadata", {}).get("space_key", "Unknown")
                            space_name1 = doc1.get("metadata", {}).get("space_name", space1)
                        st.markdown(f"**Space:** **{space_name1}**")
                    with col_space2:
                        if hasattr(doc2, 'metadata'):
                            space2 = doc2.metadata.get("space_key", "Unknown") if doc2.metadata else "Unknown"
                            space_name2 = doc2.metadata.get("space_name", space2) if doc2.metadata else space2
                        else:
                            space2 = doc2.get("metadata", {}).get("space_key", "Unknown")
                            space_name2 = doc2.get("metadata", {}).get("space_name", space2)
                        st.markdown(f"**Space:** **{space_name2}**")
                else:
                    # SharePoint information
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.markdown(f"**Platform:** SharePoint")
                        doc1_id = getattr(doc1, 'id', None) if hasattr(doc1, 'id') else doc1.get('id', 'Unknown')
                        st.markdown(f"**Document ID:** {doc1_id}")
                    with col_info2:
                        st.markdown(f"**Platform:** SharePoint")
                        doc2_id = getattr(doc2, 'id', None) if hasattr(doc2, 'id') else doc2.get('id', 'Unknown')
                        st.markdown(f"**Document ID:** {doc2_id}")
                
                # Content preview
                col_content1, col_content2 = st.columns(2)
                
                with col_content1:
                    st.markdown(f"**{title1}**")
                    
                    if platform == "confluence" and hasattr(doc1, 'page_content'):
                        content_preview = doc1.page_content[:300] + "..." if len(doc1.page_content) > 300 else doc1.page_content
                        st.markdown(f"```\n{content_preview}\n```")
                    else:
                        st.info("Content preview not available for SharePoint documents")
                    
                    # Handle source URL
                    if hasattr(doc1, 'metadata') and doc1.metadata:
                        source1 = doc1.metadata.get('source')
                    else:
                        source1 = doc1.get("metadata", {}).get('source')
                    
                    if source1:
                        st.markdown(f"🔗 [View Document]({source1})")
                    
                with col_content2:
                    st.markdown(f"**{title2}**")
                    
                    if platform == "confluence" and hasattr(doc2, 'page_content'):
                        content_preview = doc2.page_content[:300] + "..." if len(doc2.page_content) > 300 else doc2.page_content
                        st.markdown(f"```\n{content_preview}\n```")
                    else:
                        st.info("Content preview not available for SharePoint documents")
                    
                    # Handle source URL
                    if hasattr(doc2, 'metadata') and doc2.metadata:
                        source2 = doc2.metadata.get('source')
                    else:
                        source2 = doc2.get("metadata", {}).get('source')
                    
                    if source2:
                        st.markdown(f"🔗 [View Document]({source2})")
                
                # Similarity information
                st.markdown("---")
                col_sim, col_action = st.columns([2, 1])
                
                with col_sim:
                    render_similarity_meter(similarity)
                    st.markdown(f"**Similarity Score:** {similarity:.2%}")
                
                with col_action:
                    if platform == "confluence":
                        if st.button(f"🔀 Merge These Documents", key=f"detailed_merge_{i}"):
                            st.session_state.merge_docs = {
                                "main_doc": doc1,
                                "similar_doc": doc2,
                                "similarity": similarity
                            }
                            st.session_state.page = 'merge'
                            st.rerun()
                    else:
                        st.info("SharePoint merge coming soon!")
