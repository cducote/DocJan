"""
Navigation components for DocJanitor application.
"""
import streamlit as st

def initialize_navigation():
    """
    Initialize navigation-related session state variables
    """
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    if 'merge_docs' not in st.session_state:
        st.session_state.merge_docs = None
    if 'merged_content' not in st.session_state:
        st.session_state.merged_content = ""
    if 'manual_edit_mode' not in st.session_state:
        st.session_state.manual_edit_mode = False
    if 'confluence_operation_result' not in st.session_state:
        st.session_state.confluence_operation_result = None
    if 'reset_confirmation' not in st.session_state:
        st.session_state.reset_confirmation = False
    if 'reset_result' not in st.session_state:
        st.session_state.reset_result = None
    if 'available_spaces' not in st.session_state:
        st.session_state.available_spaces = None
    if 'selected_spaces' not in st.session_state:
        st.session_state.selected_spaces = ["SD"]  # Default to current space


def render_sidebar():
    """
    Render the sidebar navigation menu
    """
    with st.sidebar:
        st.title("DocJanitor")
        st.markdown("### Menu")
        
        # Navigation buttons
        if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
            
        if st.button("🔍 Search", use_container_width=True, key="nav_search"):
            st.session_state.page = 'search'
            st.rerun()
            
        if st.button("🔄 Duplicates", use_container_width=True, key="nav_duplicates"):
            st.session_state.page = 'duplicates'
            st.rerun()
            
        if st.button("📜 Merge History", use_container_width=True, key="nav_merge_history"):
            st.session_state.page = 'merge_history'
            st.rerun()
            
        if st.button("⚙️ Settings", use_container_width=True, key="nav_settings"):
            st.session_state.page = 'settings'
            st.rerun()
            
        # Space selection
        st.markdown("---")
        st.markdown("### Filter by Space")
        
        if st.session_state.available_spaces is None:
            # Load spaces if not already loaded
            from confluence.api import get_available_spaces
            st.session_state.available_spaces = get_available_spaces()
        
        # Show space selector
        if st.session_state.available_spaces:
            space_options = [space['key'] for space in st.session_state.available_spaces]
            space_labels = [f"{space['name']} ({space['key']})" for space in st.session_state.available_spaces]
            
            selected_indices = []
            for i, space_key in enumerate(space_options):
                if space_key in st.session_state.selected_spaces:
                    selected_indices.append(i)
            
            selected_spaces = st.multiselect(
                "Select spaces:",
                options=space_options,
                default=st.session_state.selected_spaces,
                format_func=lambda x: next((s['name'] for s in st.session_state.available_spaces if s['key'] == x), x)
            )
            
            if selected_spaces != st.session_state.selected_spaces:
                st.session_state.selected_spaces = selected_spaces
                st.rerun()  # Refresh with new space filter
        else:
            st.info("No spaces available or not authenticated")


def route_to_page():
    """
    Route to the appropriate page based on st.session_state.page
    """
    # Import all page renderers
    from ui.pages.dashboard import render_dashboard
    from ui.pages.search import render_search_page
    from ui.pages.duplicates import render_duplicates_page
    from ui.pages.merge_history import render_merge_history
    from ui.pages.settings import render_settings
    from ui.pages.merge import render_merge_page
    
    # Route to the appropriate page
    if st.session_state.page == 'dashboard':
        render_dashboard()
    elif st.session_state.page == 'search':
        render_search_page()
    elif st.session_state.page == 'duplicates':
        render_duplicates_page()
    elif st.session_state.page == 'merge_history':
        render_merge_history()
    elif st.session_state.page == 'settings':
        render_settings()
    elif st.session_state.page == 'merge':
        render_merge_page()
    else:
        st.error(f"Unknown page: {st.session_state.page}")
        st.session_state.page = 'dashboard'
        st.rerun()
