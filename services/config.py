"""
Configuration module for the Confluence Document Processing Service.
Centralized configuration management with environment variable support.
"""
import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # Confluence settings
    CONFLUENCE_BASE_URL: Optional[str] = os.getenv('CONFLUENCE_BASE_URL')
    CONFLUENCE_USERNAME: Optional[str] = os.getenv('CONFLUENCE_USERNAME')
    CONFLUENCE_API_TOKEN: Optional[str] = os.getenv('CONFLUENCE_API_TOKEN')
    
    # Vector store settings
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    CHROMA_PERSIST_DIRECTORY: str = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')
    
    # Processing settings
    DEFAULT_SIMILARITY_THRESHOLD: float = float(os.getenv('DEFAULT_SIMILARITY_THRESHOLD', '0.65'))
    DEFAULT_BATCH_SIZE: int = int(os.getenv('DEFAULT_BATCH_SIZE', '50'))
    
    # API settings
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    
    # CORS settings
    CORS_ORIGINS: list = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @classmethod
    def validate_required_env_vars(cls) -> list:
        """
        Validate that required environment variables are set.
        
        Returns:
            List of missing required environment variables
        """
        missing = []
        
        if not cls.OPENAI_API_KEY:
            missing.append('OPENAI_API_KEY')
        
        return missing
    
    @classmethod
    def get_confluence_config(cls) -> tuple:
        """
        Get Confluence configuration if all required variables are set.
        
        Returns:
            Tuple of (base_url, username, api_token) or None if not configured
        """
        if all([cls.CONFLUENCE_BASE_URL, cls.CONFLUENCE_USERNAME, cls.CONFLUENCE_API_TOKEN]):
            return cls.CONFLUENCE_BASE_URL, cls.CONFLUENCE_USERNAME, cls.CONFLUENCE_API_TOKEN
        return None
