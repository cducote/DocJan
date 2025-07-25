"""
Configuration settings for DocJanitor application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Confluence Configuration
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME") 
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Application Settings
DEFAULT_SIMILARITY_THRESHOLD = 0.65
DEFAULT_SEARCH_RESULTS = 5
CHROMA_PERSIST_DIRECTORY = "chroma_store"
MERGE_OPERATIONS_FILE = "merge_operations.json"

# Confluence API URLs
def get_confluence_auth():
    """Get Confluence authentication tuple"""
    return (CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)

def get_confluence_base_url():
    """Get the base Confluence URL"""
    return CONFLUENCE_BASE_URL

def validate_config():
    """Validate that all required configuration is present"""
    required_vars = [
        "CONFLUENCE_BASE_URL",
        "CONFLUENCE_USERNAME", 
        "CONFLUENCE_API_TOKEN",
        "OPENAI_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True
