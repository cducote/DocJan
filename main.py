"""
DocJanitor - Confluence Duplicate Manager

This is the main entry point for the DocJanitor application,
which helps manage and merge duplicate content in Confluence.
"""
import streamlit as st
import os
from config.settings import validate_config
from models.database import get_document_database
from ui.navigation import initialize_navigation, render_sidebar, route_to_page
from ui.components.user_selector import render_user_selector, check_user_profile_required
from ui.components.profile_setup import render_profile_setup_modal, show_profile_setup_instructions
from ui.components.login import check_authentication

def main():
    """
    Main entry point for DocJanitor application
    """
    # Set page config
    st.set_page_config(
        page_title="DocJanitor - Confluence Duplicate Manager", 
        page_icon="🧹",
        layout="wide"
    )
    
    # Check authentication first
    if not check_authentication():
        # User is not authenticated, login page is shown
        return
    
    # Check for development mode
    dev_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
    skip_login = os.getenv('SKIP_LOGIN', 'false').lower() == 'true'
    
    # Show dev mode indicator if enabled
    if dev_mode:
        with st.sidebar:
            st.markdown("🚀 **DEV MODE** 🚀")
            if st.session_state.get('user_email'):
                st.caption(f"👤 {st.session_state.user_email}")
            st.markdown("---")
    
    # Initialize navigation and session state
    initialize_navigation()
    
    # User profile management - this loads user settings into session state
    current_profile = render_user_selector()
    
    # Show profile setup if needed
    if st.session_state.get('show_profile_setup', False):
        render_profile_setup_modal()
        show_profile_setup_instructions()
        return  # Don't render the rest of the app while in setup mode
    
    # Check if user has valid profile before proceeding
    if not check_user_profile_required():
        # Show helpful getting started info
        st.title("🧹 DocJanitor")
        st.markdown("### Welcome to DocJanitor!")
        st.markdown("DocJanitor helps you find and merge duplicate content in your Confluence spaces.")
        
        st.markdown("#### 🚀 Getting Started:")
        st.markdown("1. **Create a user profile** using the sidebar")
        st.markdown("2. **Add your Confluence details** (URL and API token)")
        st.markdown("3. **Select spaces** to analyze for duplicates")
        st.markdown("4. **Find and merge** duplicate content with AI assistance")
        
        # Show API token instructions
        show_profile_setup_instructions()
        return
    
    # Validate configuration with user's settings
    try:
        validate_config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please check your profile settings and ensure all required information is provided.")
        
        # Offer to edit current profile
        if st.button("⚙️ Edit Current Profile"):
            st.session_state.edit_profile = st.session_state.get('profile_name')
            st.session_state.show_profile_setup = True
            # Don't rerun to avoid websocket issues
        return
    
    # Initialize database connection
    try:
        db = get_document_database()
        if db is None:
            st.error("Failed to connect to the document database")
            st.info("Please check your database configuration and try again.")
            return
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return
    
    # Show current user info in a small notice
    if hasattr(st.session_state, 'current_user_email'):
        st.success(f"👤 Logged in as: **{st.session_state.current_user_email}** | Profile: **{st.session_state.get('profile_name', 'Unknown')}**")
    
    # Render sidebar navigation
    render_sidebar()
    
    # Route to the appropriate page based on session state
    route_to_page()


if __name__ == "__main__":
    main()
