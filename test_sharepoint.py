"""
Quick test script for SharePoint connection using Microsoft Graph API
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SharePoint credentials from .env
SP_CLIENT_ID = os.getenv("SP_CLIENT_ID")
SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SP_TENANT_ID = os.getenv("SP_TENANT_ID")
SP_BASE_URL = os.getenv("SP_BASE_URL")

def get_access_token():
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
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")
        
        response.raise_for_status()
        
        token_info = response.json()
        print("✅ Successfully obtained access token")
        print(f"   Token type: {token_info.get('token_type')}")
        print(f"   Expires in: {token_info.get('expires_in')} seconds")
        
        return token_info.get('access_token')
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get access token: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return None

def test_sharepoint_sites():
    """Test basic SharePoint sites access"""
    access_token = get_access_token()
    if not access_token:
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Test 1: Get all sites
    print("\n🔍 Testing: Get all SharePoint sites")
    try:
        sites_url = "https://graph.microsoft.com/v1.0/sites"
        response = requests.get(sites_url, headers=headers)
        response.raise_for_status()
        
        sites_data = response.json()
        sites = sites_data.get('value', [])
        
        print(f"✅ Found {len(sites)} SharePoint sites:")
        for site in sites[:3]:  # Show first 3 sites
            print(f"   - {site.get('displayName', 'Unnamed Site')} ({site.get('webUrl', 'No URL')})")
        
        if len(sites) > 3:
            print(f"   ... and {len(sites) - 3} more sites")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get sites: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
    
    # Test 2: Get specific site (try to extract from SP_BASE_URL)
    if SP_BASE_URL:
        print(f"\n🔍 Testing: Get specific site from {SP_BASE_URL}")
        try:
            # Extract site from URL (e.g., concatly.sharepoint.com)
            domain = SP_BASE_URL.replace("https://", "").replace("http://", "").split("/")[0]
            site_url = f"https://graph.microsoft.com/v1.0/sites/{domain}"
            
            response = requests.get(site_url, headers=headers)
            response.raise_for_status()
            
            site_data = response.json()
            print(f"✅ Successfully accessed site: {site_data.get('displayName', 'Unknown')}")
            print(f"   Site ID: {site_data.get('id', 'Unknown')}")
            print(f"   Description: {site_data.get('description', 'No description')}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get specific site: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")

def main():
    """Run SharePoint connection tests"""
    print("🚀 Testing SharePoint Connection")
    print("=" * 50)
    
    # Check if credentials are loaded
    print(f"Client ID: {SP_CLIENT_ID[:8]}..." if SP_CLIENT_ID else "❌ Missing SP_CLIENT_ID")
    print(f"Tenant ID: {SP_TENANT_ID[:8]}..." if SP_TENANT_ID else "❌ Missing SP_TENANT_ID")
    print(f"Base URL: {SP_BASE_URL}" if SP_BASE_URL else "❌ Missing SP_BASE_URL")
    print(f"Client Secret: {'Set' if SP_CLIENT_SECRET else '❌ Missing SP_CLIENT_SECRET'}")
    
    if not all([SP_CLIENT_ID, SP_CLIENT_SECRET, SP_TENANT_ID]):
        print("\n❌ Missing required SharePoint credentials!")
        return
    
    test_sharepoint_sites()
    print("\n" + "=" * 50)
    print("🏁 SharePoint connection test complete!")

if __name__ == "__main__":
    main()
