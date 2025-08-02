"""
Search page for Concatly.
"""
import streamlit as st
from models.database import get_document_database
from utils.helpers import format_timestamp_to_est

def render_search_page():
    """
    Render the search page
    """
    st.title("🔍 Search Documents")
    st.markdown("Search for documents using semantic search.")
    
    # Get database
    db = get_document_database()
    
    # Search form
    with st.form("search_page_semantic_search"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Query", 
                value=st.session_state.get("search_query", ""),
                placeholder="Enter search terms..."
            )
        
        with col2:
            k_results = st.number_input(
                "Max Results", 
                min_value=1, 
                max_value=100, 
                value=st.session_state.get("k_results", 10)
            )
        
        search_button = st.form_submit_button("Search", use_container_width=True)
        
        if search_button and search_query:
            st.session_state.search_query = search_query
            st.session_state.k_results = k_results
            
            with st.spinner("Searching documents..."):
                # Perform search
                search_results = db.similarity_search_with_score(
                    search_query, 
                    k=k_results,
                    filter={"space_key": {"$in": st.session_state.selected_spaces}} if st.session_state.selected_spaces else None
                )
                
                # Store results in session state
                st.session_state.search_results = search_results
    
    # Display results if available
    if "search_results" in st.session_state and st.session_state.search_results:
        st.markdown("## Search Results")
        
        for i, (doc, score) in enumerate(st.session_state.search_results):
            similarity = 1 - score  # Convert distance to similarity
            
            # Document card
            with st.container(border=True):
                # Header with title and score
                col1, col2 = st.columns([4, 1])
                with col1:
                    title = doc.metadata.get("title", "Untitled")
                    url = doc.metadata.get("source", "")
                    if url:
                        st.markdown(f"### [{title}]({url})")
                    else:
                        st.markdown(f"### {title}")
                
                with col2:
                    st.metric("Relevance", f"{similarity:.0%}")
                
                # Metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    space = doc.metadata.get("space_key", "Unknown")
                    space_name = doc.metadata.get("space_name", space)
                    st.markdown(f"**Space:** {space_name}")
                
                with col2:
                    created = doc.metadata.get("created_date", "")
                    if created:
                        st.markdown(f"**Created:** {format_timestamp_to_est(created)}")
                
                with col3:
                    updated = doc.metadata.get("last_updated", "")
                    if updated:
                        st.markdown(f"**Updated:** {format_timestamp_to_est(updated)}")
                
                # Content preview
                with st.expander("Preview Content"):
                    st.markdown(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                
                # Actions
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("Find Similar", key=f"similar_{i}"):
                        st.session_state.search_query = ""  # Clear previous search
                        st.session_state.selected_document = doc
                        st.session_state.page = 'duplicates'
                        st.rerun()
    
    elif "search_query" in st.session_state and st.session_state.search_query:
        st.info("No results found for your search query. Try different keywords.")
