"""
Concatly - Confluence Duplicate Manager

This is the main entry point for the Concatly application,
which helps manage and merge duplicate content in Confluence.
"""

# Fix for SQLite3 version compatibility on cloud platforms
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import streamlit as st
import os
from config.settings import validate_config
from models.database import get_document_database
from ui.navigation import initialize_navigation, render_sidebar, route_to_page
from auth import require_auth, show_auth_status

def main():
    """
    Main entry point for Concatly application
    """
    # Set page config
    st.set_page_config(page_title="Concatly - Confluence Duplicate Manager", layout="wide")
    
    # Check authentication first
    if not require_auth():
        return
    
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
    
    # Show auth status in sidebar
    show_auth_status()
    
    # Render sidebar navigation
    render_sidebar()
    
    # Route to the appropriate page based on session state
    route_to_page()


if __name__ == "__main__":
    main()
