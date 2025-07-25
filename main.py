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

def main():
    """
    Main entry point for DocJanitor application
    """
    # Set page config
    st.set_page_config(page_title="DocJanitor - Confluence Duplicate Manager", layout="wide")
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please check your .env file and ensure all required variables are set.")
        st.stop()
    
    # Initialize database connection
    db = get_document_database()
    if db is None:
        st.error("Failed to connect to the document database")
        st.info("Please check your database configuration and try again.")
        st.stop()
    
    # Initialize navigation and session state
    initialize_navigation()
    
    # Render sidebar navigation
    render_sidebar()
    
    # Route to the appropriate page based on session state
    route_to_page()


if __name__ == "__main__":
    main()
