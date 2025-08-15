"""
Centralized environment configuration for Concatly.
Handles environment variables with proper fallbacks for development and production.
Supports AWS Secrets Manager for production deployments.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class ConcatlyConfig:
    """Centralized configuration management with environment variable fallbacks."""
    
    def __init__(self):
        self._secrets_cache = {}
        self._load_environment_files()
    
    def _load_environment_files(self):
        """Load environment files in priority order."""
        # Try to import dotenv for loading .env files
        try:
            from dotenv import load_dotenv
            
            # Load root .env file (backend development)
            root_env = Path(__file__).parent.parent / '.env'
            if root_env.exists():
                load_dotenv(root_env, override=False)  # Don't override existing env vars
            
            # Load NextJS .env.local (frontend development)
            nextjs_env = Path(__file__).parent.parent / 'nextjs' / '.env.local'
            if nextjs_env.exists():
                load_dotenv(nextjs_env, override=False)  # Don't override existing env vars
                
        except ImportError:
            # dotenv not available, rely on system environment variables
            pass
    
    def _get_aws_secret(self, secret_name: str, key: str = None) -> Optional[str]:
        """
        Get secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            key: Specific key within the secret (if secret contains JSON)
            
        Returns:
            Secret value or None if not available
        """
        # Check if we're in a production environment
        if not os.getenv('AWS_REGION') and not os.getenv('AWS_DEFAULT_REGION'):
            return None
            
        # Check cache first
        cache_key = f"{secret_name}:{key}" if key else secret_name
        if cache_key in self._secrets_cache:
            return self._secrets_cache[cache_key]
        
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            # Create a Secrets Manager client
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
            )
            
            # Get the secret value
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response['SecretString']
            
            # If key is specified, parse as JSON and get the key
            if key:
                secret_dict = json.loads(secret_string)
                value = secret_dict.get(key)
            else:
                value = secret_string
            
            # Cache the result
            self._secrets_cache[cache_key] = value
            return value
            
        except (ImportError, ClientError, NoCredentialsError, json.JSONDecodeError) as e:
            # boto3 not available, no AWS credentials, or secret not found
            # This is normal in development environments
            return None
    
    @property
    def openai_api_key(self) -> str:
        """
        Get OpenAI API key with fallback priority:
        1. Environment variable OPENAI_API_KEY (Vercel, local override)
        2. AWS Secrets Manager (production EKS)
        3. Kubernetes secret fallback (OPENAI_API_KEY_FALLBACK)
        4. Root .env file (backend development) 
        5. NextJS .env.local (frontend development)
        """
        # First try direct environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        # Try AWS Secrets Manager for production
        secret_name = os.getenv('OPENAI_SECRET_NAME', 'concatly/openai')
        api_key = self._get_aws_secret(secret_name, 'api_key')
        if api_key:
            return api_key
        
        # Try Kubernetes secret fallback
        api_key = os.getenv('OPENAI_API_KEY_FALLBACK')
        if api_key:
            return api_key
        
        # If we get here, no API key was found
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in:\n"
            "- Environment variable OPENAI_API_KEY (Vercel, local)\n"
            "- AWS Secrets Manager (production)\n"
            "- Kubernetes secrets (fallback)\n"
            "- Root .env file (backend dev)\n"
            "- nextjs/.env.local (frontend dev)"
        )
    
    @property
    def confluence_credentials(self) -> Dict[str, Optional[str]]:
        """
        Get Confluence credentials with AWS Secrets Manager support.
        
        Returns:
            Dict with base_url, username, api_token
        """
        # Try environment variables first
        base_url = os.getenv('CONFLUENCE_BASE_URL')
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        # Try AWS Secrets Manager if any are missing
        if not all([base_url, username, api_token]):
            secret_name = os.getenv('CONFLUENCE_SECRET_NAME', 'concatly/confluence')
            
            if not base_url:
                base_url = self._get_aws_secret(secret_name, 'base_url')
            if not username:
                username = self._get_aws_secret(secret_name, 'username')
            if not api_token:
                api_token = self._get_aws_secret(secret_name, 'api_token')
        
        return {
            'base_url': base_url,
            'username': username,
            'api_token': api_token
        }
    
    @property
    def chroma_persist_directory(self) -> str:
        """Get ChromaDB persistence directory."""
        return os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_store')
    
    @property
    def confluence_base_url(self) -> Optional[str]:
        """Get Confluence base URL."""
        return self.confluence_credentials['base_url']
    
    @property
    def confluence_username(self) -> Optional[str]:
        """Get Confluence username."""
        return self.confluence_credentials['username']
    
    @property
    def confluence_api_token(self) -> Optional[str]:
        """Get Confluence API token."""
        return self.confluence_credentials['api_token']
    
    @property
    def clerk_publishable_key(self) -> Optional[str]:
        """Get Clerk publishable key."""
        return os.getenv('CLERK_PUBLISHABLE_KEY')
    
    @property
    def clerk_secret_key(self) -> Optional[str]:
        """Get Clerk secret key."""
        return os.getenv('CLERK_SECRET_KEY')
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return os.getenv('DEBUG_AUTH', 'false').lower() == 'true'
    
    @property
    def sandbox_mode(self) -> bool:
        """Check if sandbox mode is enabled."""
        return os.getenv('SANDBOX_MODE', 'false').lower() == 'true'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return os.getenv('NODE_ENV') == 'production' or bool(os.getenv('AWS_REGION'))
    
    def validate_required_config(self) -> dict:
        """
        Validate that required configuration is available.
        Returns a status dict with validation results.
        """
        status = {
            'valid': True,
            'missing': [],
            'warnings': [],
            'environment': 'production' if self.is_production else 'development'
        }
        
        # Check required configs
        try:
            api_key = self.openai_api_key
            status['openai_source'] = 'aws_secrets' if self._get_aws_secret(os.getenv('OPENAI_SECRET_NAME', 'concatly/openai'), 'api_key') else 'environment'
        except ValueError:
            status['valid'] = False
            status['missing'].append('OPENAI_API_KEY')
        
        # Check optional but recommended configs
        if not self.confluence_base_url:
            status['warnings'].append('CONFLUENCE_BASE_URL not set')
        
        return status


# Global configuration instance
config = ConcatlyConfig()


def get_config() -> ConcatlyConfig:
    """Get the global configuration instance."""
    return config


# Convenience functions for backward compatibility
def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return config.openai_api_key


def get_chroma_persist_directory() -> str:
    """Get ChromaDB persistence directory."""
    return config.chroma_persist_directory


if __name__ == "__main__":
    # Test configuration when run directly
    print("🔧 Concatly Configuration Test")
    print("=" * 50)
    
    validation = config.validate_required_config()
    
    print(f"🌍 Environment: {validation['environment']}")
    print(f"✅ Configuration valid: {validation['valid']}")
    
    if validation['missing']:
        print(f"❌ Missing required config: {', '.join(validation['missing'])}")
    
    if validation['warnings']:
        print(f"⚠️  Warnings: {', '.join(validation['warnings'])}")
    
    print(f"📁 ChromaDB directory: {config.chroma_persist_directory}")
    print(f"📊 Log level: {config.log_level}")
    print(f"🔍 Debug mode: {config.debug_mode}")
    print(f"🏖️  Sandbox mode: {config.sandbox_mode}")
    print(f"🏭 Production mode: {config.is_production}")
    
    try:
        api_key = config.openai_api_key
        source = validation.get('openai_source', 'unknown')
        print(f"🔑 OpenAI API Key: ✅ Set (source: {source})")
    except ValueError as e:
        print(f"🔑 OpenAI API Key: ❌ {e}")
    
    # Test Confluence credentials
    confluence_creds = config.confluence_credentials
    confluence_available = all(confluence_creds.values())
    print(f"🌐 Confluence credentials: {'✅ Available' if confluence_available else '⚠️ Partial/Missing'}")
    
    if config.is_production:
        print("🔐 Production environment detected - using AWS Secrets Manager")
