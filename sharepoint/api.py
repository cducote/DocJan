"""
SharePoint API integration for Concatly

This module provides SharePoint document management functionality
using Microsoft Graph API, similar to the Confluence API module.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SharePoint credentials
SP_CLIENT_ID = os.getenv("SP_CLIENT_ID")
SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SP_TENANT_ID = os.getenv("SP_TENANT_ID")
SP_BASE_URL = os.getenv("SP_BASE_URL")

class SharePointAPI:
    def __init__(self):
        self.access_token = None
        self.site_id = None
        self.default_drive_id = None
        self.token_expires = None
        
    def get_access_token(self):
        """Get access token for Microsoft Graph API"""
        token_url = f"https://login.microsoftonline.com/{SP_TENANT_ID}/oauth2/v2.0/token"
        
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': SP_CLIENT_ID,
            'client_secret': SP_CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_info = response.json()
            self.access_token = token_info.get('access_token')
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to get access token: {e}")
            return False

    def get_site_info(self):
        """Get site ID and default drive ID"""
        if not self.access_token:
            if not self.get_access_token():
                return False
                
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            # Get site info
            domain = SP_BASE_URL.replace("https://", "").replace("http://", "").split("/")[0]
            site_url = f"https://graph.microsoft.com/v1.0/sites/{domain}"
            
            response = requests.get(site_url, headers=headers)
            response.raise_for_status()
            
            site_data = response.json()
            self.site_id = site_data.get('id')
            
            # Get default drive (Documents library)
            drive_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive"
            response = requests.get(drive_url, headers=headers)
            response.raise_for_status()
            
            drive_data = response.json()
            self.default_drive_id = drive_data.get('id')
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to get site info: {e}")
            return False

    def get_documents(self, folder_name=None):
        """Get documents from SharePoint site"""
        if not self.access_token or not self.default_drive_id:
            if not self.get_access_token() or not self.get_site_info():
                return []
                
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            if folder_name:
                # Get documents from specific folder
                url = f"https://graph.microsoft.com/v1.0/drives/{self.default_drive_id}/root:/{folder_name}:/children"
            else:
                # Get documents from root
                url = f"https://graph.microsoft.com/v1.0/drives/{self.default_drive_id}/root/children"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            documents = []
            
            for item in data.get('value', []):
                if 'file' in item:  # Only files, not folders
                    documents.append({
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'size': item.get('size', 0),
                        'last_modified': item.get('lastModifiedDateTime'),
                        'web_url': item.get('webUrl'),
                        'download_url': item.get('@microsoft.graph.downloadUrl')
                    })
            
            return documents
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to get documents: {e}")
            return []

    def get_document_content(self, document_id):
        """Get content of a specific document"""
        if not self.access_token or not self.default_drive_id:
            if not self.get_access_token() or not self.get_site_info():
                return None
                
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            # Get download URL
            url = f"https://graph.microsoft.com/v1.0/drives/{self.default_drive_id}/items/{document_id}/content"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Try to decode as text
            try:
                content = response.content.decode('utf-8')
                return content
            except UnicodeDecodeError:
                # If not text, return basic info
                return f"Binary file - {len(response.content)} bytes"
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to get document content: {e}")
            return None

    def get_folders(self):
        """Get folders from SharePoint site"""
        if not self.access_token or not self.default_drive_id:
            if not self.get_access_token() or not self.get_site_info():
                return []
                
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            url = f"https://graph.microsoft.com/v1.0/drives/{self.default_drive_id}/root/children"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            folders = []
            
            for item in data.get('value', []):
                if 'folder' in item:  # Only folders, not files
                    folders.append({
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'web_url': item.get('webUrl'),
                        'child_count': item.get('folder', {}).get('childCount', 0)
                    })
            
            return folders
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to get folders: {e}")
            return []

# Global SharePoint API instance
sharepoint_api = SharePointAPI()
