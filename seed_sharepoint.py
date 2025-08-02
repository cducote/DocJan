"""
SharePoint Seed Script - Create test documents for duplicate testing

This script creates mock documents in SharePoint to test duplicate detection
and merging functionality, similar to the Confluence seed script.
"""
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SharePoint credentials
SP_CLIENT_ID = os.getenv("SP_CLIENT_ID")
SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET")
SP_TENANT_ID = os.getenv("SP_TENANT_ID")
SP_BASE_URL = os.getenv("SP_BASE_URL")

class SharePointSeeder:
    def __init__(self):
        self.access_token = None
        self.site_id = None
        self.default_drive_id = None
        
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
            print(f"✅ Successfully obtained access token")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get access token: {e}")
            return False

    def get_site_info(self):
        """Get site ID and default drive ID"""
        if not self.access_token:
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
            print(f"✅ Got site ID: {self.site_id}")
            
            # Get default drive (Documents library)
            drive_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive"
            response = requests.get(drive_url, headers=headers)
            response.raise_for_status()
            
            drive_data = response.json()
            self.default_drive_id = drive_data.get('id')
            print(f"✅ Got default drive ID: {self.default_drive_id}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get site info: {e}")
            return False

    def create_folder(self, folder_name, parent_path="root"):
        """Create a folder in SharePoint"""
        if not self.access_token or not self.default_drive_id:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        folder_data = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        
        try:
            url = f"https://graph.microsoft.com/v1.0/drives/{self.default_drive_id}/items/{parent_path}/children"
            response = requests.post(url, headers=headers, json=folder_data)
            response.raise_for_status()
            
            folder_info = response.json()
            print(f"✅ Created folder: {folder_name}")
            return folder_info.get('id')
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create folder {folder_name}: {e}")
            return None

    def create_text_file(self, filename, content, folder_id="root"):
        """Create a text file in SharePoint"""
        if not self.access_token or not self.default_drive_id:
            return False
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'text/plain'
        }
        
        try:
            url = f"https://graph.microsoft.com/v1.0/drives/{self.default_drive_id}/items/{folder_id}:/{filename}:/content"
            response = requests.put(url, headers=headers, data=content.encode('utf-8'))
            response.raise_for_status()
            
            print(f"✅ Created file: {filename}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create file {filename}: {e}")
            return False

    def seed_documents(self):
        """Create test documents with duplicate patterns"""
        
        # Create test folder
        test_folder_id = self.create_folder("Concatly_Test_Documents")
        if not test_folder_id:
            print("❌ Failed to create test folder, using root")
            test_folder_id = "root"
        
        # Define test documents with similarity patterns
        documents = [
            # Document 1 & 2 - Similar content (password reset instructions)
            {
                "filename": "Password_Reset_Guide_v1.txt",
                "content": """Password Reset Instructions

How to Reset Your Password:

1. Go to the login page
2. Click "Forgot Password" link  
3. Enter your email address
4. Check your email for reset instructions
5. Click the reset link in the email
6. Create a new strong password

Note: Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters.

This procedure applies to all system accounts and ensures secure access recovery.
Contact IT support if you experience any issues during the reset process.
"""
            },
            {
                "filename": "How_to_Reset_Password_v2.txt", 
                "content": """Password Reset Procedure

Steps to Reset Your Password:

1. Navigate to the login page
2. Select "Forgot Password" option
3. Provide your email address
4. Check your email for reset instructions
5. Click on the reset link in the email
6. Set up a new secure password

Important: Password must be minimum 8 characters with uppercase, lowercase, numbers, and special characters.

This process works for all system accounts and provides secure access recovery.
Please contact IT support if you encounter any problems during password reset.
"""
            },
            
            # Document 3 & 4 - Similar content (meeting guidelines)
            {
                "filename": "Meeting_Guidelines_2024.txt",
                "content": """Meeting Guidelines and Best Practices

Effective Meeting Management:

1. Schedule meetings with clear agendas
2. Invite only necessary participants
3. Start and end meetings on time
4. Encourage active participation from all attendees
5. Take detailed meeting notes
6. Follow up with action items and deadlines

Meeting Etiquette:
- Arrive on time and prepared
- Mute microphones when not speaking
- Stay focused on agenda topics
- Respect speaking time limits
- Ask clarifying questions when needed

These guidelines help ensure productive and efficient meetings for all team members.
"""
            },
            {
                "filename": "Best_Practices_for_Meetings.txt",
                "content": """Meeting Best Practices Guide

Guidelines for Effective Meetings:

1. Create meetings with detailed agendas
2. Only invite essential participants
3. Begin and conclude meetings punctually
4. Promote active engagement from attendees
5. Document meeting discussions thoroughly
6. Distribute action items with due dates

Professional Meeting Conduct:
- Be punctual and well-prepared
- Use mute function when not talking
- Focus on scheduled agenda items
- Observe time limits for discussions
- Seek clarification when necessary

Following these practices ensures meetings are productive and valuable for all team members.
"""
            },
            
            # Document 5 - Unique content (security policy)
            {
                "filename": "Information_Security_Policy.txt",
                "content": """Information Security Policy

Data Protection Requirements:

1. Use strong, unique passwords for all accounts
2. Enable two-factor authentication where available
3. Keep software and systems updated
4. Report security incidents immediately
5. Protect sensitive information appropriately
6. Use approved cloud storage services only
7. Secure physical devices and workspaces

Compliance Standards:
- Follow industry security frameworks
- Conduct regular security training
- Maintain audit trails for access
- Implement least privilege access
- Review and update policies annually

This policy ensures protection of company and client data assets.
All employees must adhere to these security requirements.
"""
            },
            
            # Document 6 - Unique content (remote work policy)
            {
                "filename": "Remote_Work_Policy.txt",
                "content": """Remote Work Policy and Guidelines

Working from Home Requirements:

1. Maintain consistent work schedule and availability
2. Ensure reliable internet connection and equipment
3. Create dedicated workspace free from distractions
4. Participate actively in virtual meetings and collaboration
5. Communicate regularly with team members and managers
6. Protect confidential information in home environment
7. Report technical issues promptly to IT support

Performance Expectations:
- Meet all job responsibilities and deadlines
- Maintain professional communication standards
- Use approved collaboration tools and platforms
- Track time and productivity accurately
- Balance work-life boundaries effectively

This policy supports flexible work arrangements while maintaining business operations.
Regular review ensures policy remains effective for remote workforce.
"""
            }
        ]
        
        # Create all documents
        success_count = 0
        for doc in documents:
            if self.create_text_file(doc["filename"], doc["content"], test_folder_id):
                success_count += 1
                time.sleep(1)  # Rate limiting
        
        print(f"\n📄 Created {success_count}/{len(documents)} test documents")
        return success_count

def main():
    """Main execution function"""
    print("🚀 SharePoint Seeder - Creating Test Documents")
    print("=" * 60)
    
    # Check credentials
    if not all([SP_CLIENT_ID, SP_CLIENT_SECRET, SP_TENANT_ID, SP_BASE_URL]):
        print("❌ Missing SharePoint credentials in .env file!")
        return
    
    # Initialize seeder
    seeder = SharePointSeeder()
    
    # Get authentication
    if not seeder.get_access_token():
        print("❌ Failed to authenticate with SharePoint")
        return
    
    # Get site information
    if not seeder.get_site_info():
        print("❌ Failed to get SharePoint site information")
        return
    
    # Create test documents
    print("\n📝 Creating test documents...")
    docs_created = seeder.seed_documents()
    
    print("\n" + "=" * 60)
    print(f"🏁 SharePoint seeding complete!")
    print(f"   Documents created: {docs_created}")
    print(f"   Location: {SP_BASE_URL}")
    print("   Check the 'Concatly_Test_Documents' folder")

if __name__ == "__main__":
    main()
