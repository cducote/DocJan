"""
Search page for Concatly.
"""
import streamlit as st
from fuzzywuzzy import fuzz, process
from models.database import get_document_database
from utils.helpers import format_timestamp_to_est

def render_search_page():
    """
    Render the search page
    """
    st.title("🔍 Search Documents")
    st.markdown("Search for documents using semantic search and fuzzy matching.")
    
    # Get database
    db = get_document_database()
    
    # Search form
    with st.form("search_page_semantic_search"):
        col1, col2, col3 = st.columns([3, 1, 1])
        
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
        
        with col3:
            search_type = st.selectbox(
                "Search Type",
                options=["Semantic", "Fuzzy", "Hybrid"],
                index=["Semantic", "Fuzzy", "Hybrid"].index(st.session_state.get("search_type", "Fuzzy"))
            )
        
        search_button = st.form_submit_button("Search", use_container_width=True)
        
        if search_button and search_query:
            st.session_state.search_query = search_query
            st.session_state.k_results = k_results
            st.session_state.search_type = search_type
            
            with st.spinner("Searching documents..."):
                # Perform search based on type
                if search_type == "Semantic":
                    search_results = _perform_semantic_search(db, search_query, k_results)
                elif search_type == "Fuzzy":
                    search_results = _perform_fuzzy_search(db, search_query, k_results)
                else:  # Hybrid
                    search_results = _perform_hybrid_search(db, search_query, k_results)
                
                # Store results in session state
                st.session_state.search_results = search_results
    
    # Display results if available
    if "search_results" in st.session_state and st.session_state.search_results:
        st.markdown("## Search Results")
        
        for i, (doc, score) in enumerate(st.session_state.search_results):
            similarity = 1 - score  # Convert distance to similarity
            
            # Document card
            with st.container(border=True):
                # Header with title
                title = doc.metadata.get("title", "Untitled")
                url = doc.metadata.get("source", "")
                if url:
                    st.markdown(f"### [{title}]({url})")
                else:
                    st.markdown(f"### {title}")
                
                # Metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    space_key = doc.metadata.get("space_key", "Unknown")
                    # Get the proper space name using the utility function
                    from models.database import get_space_name_from_key
                    space_name = get_space_name_from_key(space_key)
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


def _perform_semantic_search(db, search_query, k_results):
    """Perform semantic search using ChromaDB similarity search"""
    return db.similarity_search_with_score(
        search_query, 
        k=k_results,
        filter={"space_key": {"$in": st.session_state.selected_spaces}} if st.session_state.selected_spaces else None
    )


def _perform_fuzzy_search(db, search_query, k_results):
    """Perform fuzzy string matching search"""
    # Get all documents
    all_docs = db.get(include=['documents', 'metadatas'])
    
    if not all_docs['documents']:
        return []
    
    # Create searchable text for each document (title + content)
    searchable_texts = []
    doc_indices = []
    
    for i, (doc_content, metadata) in enumerate(zip(all_docs['documents'], all_docs['metadatas'])):
        # Apply space filter if selected
        if st.session_state.selected_spaces and metadata.get('space_key') not in st.session_state.selected_spaces:
            continue
            
        title = metadata.get('title', '')
        searchable_text = f"{title} {doc_content}"
        searchable_texts.append(searchable_text)
        doc_indices.append(i)
    
    if not searchable_texts:
        return []
    
    # Use fuzzy matching to find best matches
    matches = process.extract(search_query, searchable_texts, limit=k_results, scorer=fuzz.WRatio)
    
    # Convert to the expected format (doc, score)
    results = []
    for match_text, score in matches:
        # Find the original document index
        match_index = searchable_texts.index(match_text)
        original_index = doc_indices[match_index]
        
        # Create a document object similar to ChromaDB format
        from langchain_core.documents import Document
        doc = Document(
            page_content=all_docs['documents'][original_index],
            metadata=all_docs['metadatas'][original_index]
        )
        
        # Convert fuzzy score (0-100) to distance score (0-1, where 0 is perfect match)
        distance_score = (100 - score) / 100
        results.append((doc, distance_score))
    
    return results


def _perform_hybrid_search(db, search_query, k_results):
    """Perform hybrid search combining semantic and fuzzy matching"""
    # Get semantic results
    semantic_results = _perform_semantic_search(db, search_query, k_results * 2)
    
    # Get fuzzy results
    fuzzy_results = _perform_fuzzy_search(db, search_query, k_results * 2)
    
    # Combine and deduplicate results
    combined_results = {}
    
    # Add semantic results with weight
    for doc, score in semantic_results:
        doc_id = doc.metadata.get('id', doc.page_content[:100])
        # Semantic score is already a distance (lower is better)
        combined_results[doc_id] = (doc, score * 0.6)  # 60% weight for semantic
    
    # Add fuzzy results with weight
    for doc, score in fuzzy_results:
        doc_id = doc.metadata.get('id', doc.page_content[:100])
        if doc_id in combined_results:
            # Combine scores
            existing_doc, existing_score = combined_results[doc_id]
            combined_score = existing_score + (score * 0.4)  # 40% weight for fuzzy
            combined_results[doc_id] = (existing_doc, combined_score)
        else:
            combined_results[doc_id] = (doc, score * 0.4)
    
    # Sort by combined score and return top k results
    sorted_results = sorted(combined_results.values(), key=lambda x: x[1])
    return sorted_results[:k_results]
