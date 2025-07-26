"""
Configuration settings for DocJanitor application.
Supports both environment variables and user profile-based configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration (still from .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Application Settings
DEFAULT_SIMILARITY_THRESHOLD = 0.65
DEFAULT_SEARCH_RESULTS = 5
CHROMA_PERSIST_DIRECTORY = "chroma_store"
MERGE_OPERATIONS_FILE = "merge_operations.json"

def get_confluence_auth():
    """Get Confluence authentication tuple from session state or env vars"""
    # Try to get from session state first (user profiles)
    try:
        import streamlit as st
        if hasattr(st.session_state, 'current_user_email') and hasattr(st.session_state, 'api_token'):
            return (st.session_state.current_user_email, st.session_state.api_token)
    except ImportError:
        pass
    
    # Fallback to environment variables
    username = os.getenv("CONFLUENCE_USERNAME")
    token = os.getenv("CONFLUENCE_API_TOKEN")
    if username and token:
        return (username, token)
    
    raise ValueError("No Confluence authentication found in session state or environment variables")

def get_confluence_base_url():
    """Get the base Confluence URL from session state or env vars"""
    # Try to get from session state first (user profiles)
    try:
        import streamlit as st
        if hasattr(st.session_state, 'confluence_url') and st.session_state.confluence_url:
            return st.session_state.confluence_url
    except ImportError:
        pass
    
    # Fallback to environment variables
    url = os.getenv("CONFLUENCE_BASE_URL")
    if url:
        return url
    
    raise ValueError("No Confluence base URL found in session state or environment variables")

def get_user_preferences():
    """Get user preferences from session state"""
    try:
        import streamlit as st
        return getattr(st.session_state, 'user_preferences', {})
    except ImportError:
        return {}

def get_similarity_threshold():
    """Get similarity threshold from user preferences or default"""
    preferences = get_user_preferences()
    return preferences.get('default_similarity', DEFAULT_SIMILARITY_THRESHOLD)

def validate_config():
    """Validate that all required configuration is present"""
    missing = []
    
    # Check OpenAI API key (required)
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY (in .env file)")
    
    # Check Confluence settings (from session state or env)
    try:
        get_confluence_auth()
    except ValueError:
        missing.append("Confluence authentication (user profile or .env)")
    
    try:
        get_confluence_base_url()
    except ValueError:
        missing.append("Confluence base URL (user profile or .env)")
    
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")
    
    return True

# Legacy support - these will use fallbacks for backward compatibility
def get_legacy_confluence_settings():
    """Get Confluence settings in legacy format for existing code"""
    try:
        return {
            'CONFLUENCE_BASE_URL': get_confluence_base_url(),
            'CONFLUENCE_USERNAME': get_confluence_auth()[0],
            'CONFLUENCE_API_TOKEN': get_confluence_auth()[1]
        }
    except ValueError:
        return {
            'CONFLUENCE_BASE_URL': None,
            'CONFLUENCE_USERNAME': None,
            'CONFLUENCE_API_TOKEN': None
        }
