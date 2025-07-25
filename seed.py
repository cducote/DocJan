# seed.py - Script to populate Confluence spaces with mock documents for duplicate testing

from atlassian import Confluence
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Set up Confluence connection
confluence = Confluence(
    url=os.getenv("CONFLUENCE_BASE_URL"),
    username=os.getenv("CONFLUENCE_USERNAME"),
    password=os.getenv("CONFLUENCE_API_TOKEN"),
    cloud=True
)

# Define the spaces to populate
SPACES = {
    "SD": "SD",
    "PERSONAL": "~70121465f64cb86d84c92b0bdbc36762f880c"
}

# Mock documents data organized by space with similarity patterns
# Pattern:
# - Pages 1&2 in each space are similar to each other (within space)
# - Page 3 in SD is similar to Page 3 in PERSONAL (cross-space)
# - Pages 4&5 are unique in each space

documents_by_space = {
    "SD": [
        # SD Page 1 - Similar to SD Page 2 (within space similarity)
        {
            "title": "Password Reset Instructions - SD",
            "content": """
            <h2>How to Reset Your Password</h2>
            <p>Follow these steps to reset your password in the SD system:</p>
            <ol>
                <li>Go to the login page</li>
                <li>Click "Forgot Password" link</li>
                <li>Enter your email address</li>
                <li>Check your email for reset instructions</li>
                <li>Click the reset link in the email</li>
                <li>Create a new strong password</li>
            </ol>
            <p><strong>Note:</strong> Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters.</p>
            <p>This procedure applies to all SD system accounts and ensures secure access recovery.</p>
            """
        },
        # SD Page 2 - Similar to SD Page 1 (within space similarity)
        {
            "title": "Account Password Recovery - SD",
            "content": """
            <h2>Recovering Your Account Password</h2>
            <p>If you've forgotten your password for the SD system, here's how to recover it:</p>
            <ol>
                <li>Navigate to the main login screen</li>
                <li>Select "Forgot your password?" option</li>
                <li>Provide your registered email address</li>
                <li>Look for recovery email in your inbox</li>
                <li>Follow the secure reset link provided</li>
                <li>Set up a new secure password</li>
            </ol>
            <p><strong>Security Tip:</strong> Use a combination of letters, numbers, and symbols. Make it at least 8 characters long.</p>
            <p>This recovery process is standard for all SD user accounts and maintains system security.</p>
            """
        },
        # SD Page 3 - Similar to PERSONAL Page 3 (cross-space similarity)
        {
            "title": "API Documentation - User Management",
            "content": """
            <h2>User Management API</h2>
            <p>This API allows you to manage user accounts programmatically across systems.</p>
            <h3>Authentication</h3>
            <p>All API requests require authentication using API keys or tokens.</p>
            <code>Authorization: Bearer YOUR_API_KEY</code>
            <h3>Core Endpoints</h3>
            <h4>GET /api/users</h4>
            <p>Retrieve a list of all users in the system.</p>
            <h4>POST /api/users</h4>
            <p>Create a new user account with specified permissions.</p>
            <h4>PUT /api/users/{id}</h4>
            <p>Update an existing user account and its properties.</p>
            <h4>DELETE /api/users/{id}</h4>
            <p>Delete a user account from the system permanently.</p>
            <p>This API provides comprehensive user management capabilities for administrative tasks.</p>
            """
        },
        # SD Page 4 - Similar to SD Page 5 (second within-space pair for SD)
        {
            "title": "SD System Troubleshooting Guide",
            "content": """
            <h2>SD System Issues and Solutions</h2>
            <p>This document covers frequently encountered problems specific to the SD system environment.</p>
            <h3>Common SD Login Problems</h3>
            <p><strong>Issue:</strong> Cannot access the SD system dashboard</p>
            <p><strong>Solution:</strong> Verify your SD credentials, clear browser cache, or reset your SD password through the admin panel.</p>
            <h3>SD Performance Issues</h3>
            <p><strong>Issue:</strong> SD application running slowly or timing out</p>
            <p><strong>Solution:</strong> Close unnecessary SD modules, restart the SD client, or contact SD support.</p>
            <h3>SD Network Connectivity</h3>
            <p><strong>Issue:</strong> Cannot connect to SD servers</p>
            <p><strong>Solution:</strong> Check SD network settings, restart SD network adapter, or contact SD administrator.</p>
            <h3>SD Database Issues</h3>
            <p><strong>Issue:</strong> SD data not syncing properly</p>
            <p><strong>Solution:</strong> Force sync in SD settings, clear SD cache, or restart SD services.</p>
            """
        },
        # SD Page 5 - Similar to SD Page 4 (second within-space pair for SD)
        {
            "title": "SD Project Setup and Configuration",
            "content": """
            <h2>SD System Configuration and Project Setup</h2>
            <p>This guide covers setting up the SD development environment and resolving configuration issues.</p>
            <h3>SD Configuration Problems</h3>
            <p><strong>Issue:</strong> SD project not starting correctly</p>
            <p><strong>Solution:</strong> Verify SD configuration files, check SD environment variables, or reset SD project settings.</p>
            <h3>SD Environment Issues</h3>
            <p><strong>Issue:</strong> SD development environment not responding</p>
            <p><strong>Solution:</strong> Restart SD services, clear SD temporary files, or contact SD technical support.</p>
            <h3>SD Setup Connectivity</h3>
            <p><strong>Issue:</strong> Cannot connect SD to required services</p>
            <p><strong>Solution:</strong> Check SD connection settings, restart SD components, or verify SD network configuration.</p>
            <h3>SD Project Database Issues</h3>
            <p><strong>Issue:</strong> SD project database connection failing</p>
            <p><strong>Solution:</strong> Verify SD database credentials, restart SD database service, or contact SD database administrator.</p>
            """
        }
    ],
    "PERSONAL": [
        # PERSONAL Page 1 - Similar to PERSONAL Page 2 (within space similarity)
        {
            "title": "Software Installation Guide - Personal",
            "content": """
            <h2>Installing Personal Software Applications</h2>
            <p>This guide covers the installation of essential personal development tools.</p>
            <h3>Prerequisites</h3>
            <ul>
                <li>Windows 10 or later</li>
                <li>Administrator privileges on personal machine</li>
                <li>Internet connection</li>
                <li>Personal license keys where required</li>
            </ul>
            <h3>Installation Steps</h3>
            <ol>
                <li>Download the installer from the official website</li>
                <li>Run the installer as administrator</li>
                <li>Follow the setup wizard carefully</li>
                <li>Enter personal license information</li>
                <li>Restart your computer when prompted</li>
            </ol>
            <p>If you encounter any issues, consult the personal software documentation or community forums.</p>
            """
        },
        # PERSONAL Page 2 - Similar to PERSONAL Page 1 (within space similarity)
        {
            "title": "Application Installation Manual - Personal",
            "content": """
            <h2>How to Install Personal Applications</h2>
            <p>Step-by-step guide for installing necessary personal software tools.</p>
            <h3>System Requirements</h3>
            <ul>
                <li>Windows 10 or newer version</li>
                <li>Admin access to the personal system</li>
                <li>Stable internet connection</li>
                <li>Valid personal software licenses</li>
            </ul>
            <h3>Installation Process</h3>
            <ol>
                <li>Get the installer from the official source</li>
                <li>Execute installer with admin rights</li>
                <li>Complete the installation wizard</li>
                <li>Configure personal settings</li>
                <li>Reboot system if required</li>
            </ol>
            <p>For technical difficulties with personal software, check online documentation or user communities.</p>
            """
        },
        # PERSONAL Page 3 - Similar to SD Page 3 (cross-space similarity)
        {
            "title": "REST API Guide - Account Management",
            "content": """
            <h2>Account Management REST API</h2>
            <p>Comprehensive guide for managing user accounts via REST API in personal projects.</p>
            <h3>Security</h3>
            <p>API access requires valid authentication tokens for secure operations.</p>
            <code>Authorization: Token YOUR_ACCESS_TOKEN</code>
            <h3>Available Endpoints</h3>
            <h4>GET /api/accounts</h4>
            <p>Fetch list of user accounts from the system.</p>
            <h4>POST /api/accounts</h4>
            <p>Register a new user account with required details.</p>
            <h4>PATCH /api/accounts/{id}</h4>
            <p>Modify existing account details and permissions.</p>
            <h4>DELETE /api/accounts/{id}</h4>
            <p>Remove user account from system database.</p>
            <p>This API enables full account management functionality for personal applications.</p>
            """
        },
        # PERSONAL Page 4 - Similar to PERSONAL Page 5 (second within-space pair for PERSONAL)
        {
            "title": "Personal Development Environment Setup",
            "content": """
            <h2>Personal Development Environment Configuration</h2>
            <p>Complete guide for establishing and troubleshooting personal development workspace at home.</p>
            <h3>Personal Environment Issues</h3>
            <p><strong>Problem:</strong> Personal development environment not starting correctly</p>
            <p><strong>Resolution:</strong> Check personal environment variables, restart personal development services, or reset personal configuration files.</p>
            <h3>Personal Configuration Problems</h3>
            <p><strong>Problem:</strong> Personal project configuration failing</p>
            <p><strong>Resolution:</strong> Verify personal settings files, clear personal cache, or reinstall personal dependencies.</p>
            <h3>Personal IDE Issues</h3>
            <p><strong>Problem:</strong> Personal IDE not responding or crashing</p>
            <p><strong>Resolution:</strong> Restart personal IDE, update personal extensions, or reset personal workspace settings.</p>
            <h3>Personal Project Issues</h3>
            <p><strong>Problem:</strong> Personal projects not building or running</p>
            <p><strong>Resolution:</strong> Check personal build configuration, update personal project dependencies, or contact personal development support.</p>
            """
        },
        # PERSONAL Page 5 - Similar to PERSONAL Page 4 (second within-space pair for PERSONAL)
        {
            "title": "Personal Problem Resolution Guide",
            "content": """
            <h2>Personal System Problem Resolution</h2>
            <p>Quick reference for solving common personal technical and development issues at home.</p>
            <h3>Personal Development Authentication Failures</h3>
            <p><strong>Problem:</strong> Unable to access personal development applications</p>
            <p><strong>Resolution:</strong> Check personal development credentials, clear personal browser data, or reset personal development passwords.</p>
            <h3>Personal Development Performance</h3>
            <p><strong>Problem:</strong> Personal development applications running slowly</p>
            <p><strong>Resolution:</strong> Close personal background processes, restart personal development environment, or upgrade personal hardware.</p>
            <h3>Personal Development Network Issues</h3>
            <p><strong>Problem:</strong> Personal development network access problems</p>
            <p><strong>Resolution:</strong> Check personal development network settings, restart personal network adapter, or contact personal ISP.</p>
            <h3>Personal Development Storage Issues</h3>
            <p><strong>Problem:</strong> Running out of personal development storage space</p>
            <p><strong>Resolution:</strong> Clean personal temporary files, archive personal old development projects, or upgrade personal storage.</p>
            """
        }
    ]
}

def create_page(space_key, title, content):
    """Create a page in Confluence"""
    try:
        # Check if page already exists
        existing_page = confluence.get_page_by_title(space_key, title)
        if existing_page:
            print(f">> Page '{title}' already exists in {space_key}. Skipping...")
            return False
        
        # Create the page
        page = confluence.create_page(
            space=space_key,
            title=title,
            body=content,
            parent_id=None,
            type='page',
            representation='storage'
        )
        print(f">> Created page: '{title}' in space {space_key}")
        return True
    except Exception as e:
        print(f">> Error creating page '{title}' in {space_key}: {str(e)}")
        return False

def main():
    """Main function to seed the Confluence spaces"""
    print(">> Starting Confluence spaces seeding...")
    print(f">> Target spaces: {list(SPACES.keys())}")
    
    total_pages = sum(len(docs) for docs in documents_by_space.values())
    print(f">> Total pages to create: {total_pages}")
    print("-" * 60)
    
    overall_created = 0
    overall_skipped = 0
    
    for space_name, space_key in SPACES.items():
        print(f"\n>> Processing space: {space_name} ({space_key})")
        docs = documents_by_space[space_name]
        print(f">> Pages in this space: {len(docs)}")
        print("-" * 40)
        
        space_created = 0
        space_skipped = 0
        
        for i, doc in enumerate(docs, 1):
            print(f"[{space_name} {i}/{len(docs)}] Creating: {doc['title']}")
            
            if create_page(space_key, doc['title'], doc['content']):
                space_created += 1
                overall_created += 1
            else:
                space_skipped += 1
                overall_skipped += 1
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(1)
        
        print(f">> {space_name} Summary: {space_created} created, {space_skipped} skipped")
    
    print("\n" + "=" * 60)
    print(">> OVERALL SEEDING SUMMARY:")
    print(f">> Total pages created: {overall_created}")
    print(f">> Total pages skipped: {overall_skipped}")
    print(f">> Total processed: {total_pages}")
    print("\n>> Similarity Pattern Created:")
    print(">>   - SD Pages 1&2 are similar (within space)")
    print(">>   - SD Pages 4&5 are similar (within space)")  
    print(">>   - PERSONAL Pages 1&2 are similar (within space)")
    print(">>   - PERSONAL Pages 4&5 are similar (within space)")
    print(">>   - SD Page 3 is similar to PERSONAL Page 3 (cross-space)")
    print(">>   - Expected: 5 duplicate pairs total")
    
    # Run duplicate detection if any pages were created
    if overall_created > 0:
        print("\n" + "=" * 60)
        print(">> LOADING DOCUMENTS INTO CHROMADB...")
        print(">> This will pull the created pages into the vector database...")
        
        try:
            # Import the loading function
            from confluence.api import load_documents_from_spaces
            
            # Wait a moment for Confluence to fully save the pages
            print(">> Waiting for Confluence pages to be ready...")
            time.sleep(3)
            
            # Load documents from both spaces
            space_keys = list(SPACES.values())  # ["SD", "~70121465f64cb86d84c92b0bdbc36762f880c"]
            
            print(f">> Loading documents from spaces: {space_keys}")
            load_result = load_documents_from_spaces(space_keys, limit_per_space=50)
            
            if load_result:
                print(f">> ✅ Successfully loaded {load_result} documents into ChromaDB")
            else:
                print(">> ❌ No documents were loaded into ChromaDB")
                
        except ImportError as e:
            print(f">> ❌ Could not import document loading: {e}")
            print(">> You may need to load documents manually from the app")
        except Exception as e:
            print(f">> ❌ Error during document loading: {e}")
            print(">> You may need to load documents manually from the app")
        
        print("\n" + "=" * 60)
        print(">> RUNNING DUPLICATE DETECTION...")
        print(">> This will analyze documents and detect similarities...")
        
        try:
            # Import the scan function
            from models.database import scan_for_duplicates
            
            # Wait a moment for documents to be fully indexed
            print(">> Waiting for documents to be indexed...")
            time.sleep(5)
            
            # Run the duplicate scan
            scan_result = scan_for_duplicates(similarity_threshold=0.65, update_existing=True)
            
            if scan_result['success']:
                print(f">> ✅ Duplicate scan completed successfully!")
                print(f">>    - {scan_result['pairs_found']} duplicate pairs found")
                print(f">>    - {scan_result['documents_updated']} documents updated")
                print(f">>    - Threshold used: {scan_result.get('threshold_used', 0.65)}")
                
                if scan_result['pairs_found'] >= 5:
                    print(">> 🎯 Expected 5 duplicate pairs found - Perfect!")
                elif scan_result['pairs_found'] > 0:
                    print(f">> ⚠️  Found {scan_result['pairs_found']} pairs, expected 5")
                else:
                    print(">> ❌ No duplicate pairs found - check document content similarity")
            else:
                print(f">> ❌ Duplicate scan failed: {scan_result['message']}")
                
        except ImportError as e:
            print(f">> ❌ Could not import duplicate detection: {e}")
            print(">> You may need to run duplicate detection manually from the app")
        except Exception as e:
            print(f">> ❌ Error during duplicate detection: {e}")
            print(">> You may need to run duplicate detection manually from the app")
    
    print(">> Seeding complete!")

if __name__ == "__main__":
    main()
