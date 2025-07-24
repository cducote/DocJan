# seed.py - Script to populate Confluence space with mock documents

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

# Define the space key
SPACE_KEY = "SD"

# Mock documents data
documents = [
    # First 5 unique documents
    {
        "title": "Password Reset Instructions",
        "content": """
        <h2>How to Reset Your Password</h2>
        <p>Follow these steps to reset your password:</p>
        <ol>
            <li>Go to the login page</li>
            <li>Click "Forgot Password" link</li>
            <li>Enter your email address</li>
            <li>Check your email for reset instructions</li>
            <li>Click the reset link in the email</li>
            <li>Create a new strong password</li>
        </ol>
        <p><strong>Note:</strong> Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters.</p>
        """
    },
    {
        "title": "Software Installation Guide",
        "content": """
        <h2>Installing Required Software</h2>
        <p>This guide covers the installation of essential development tools.</p>
        <h3>Prerequisites</h3>
        <ul>
            <li>Windows 10 or later</li>
            <li>Administrator privileges</li>
            <li>Internet connection</li>
        </ul>
        <h3>Installation Steps</h3>
        <ol>
            <li>Download the installer from the official website</li>
            <li>Run the installer as administrator</li>
            <li>Follow the setup wizard</li>
            <li>Restart your computer when prompted</li>
        </ol>
        <p>If you encounter any issues, please contact the IT support team.</p>
        """
    },
    {
        "title": "API Documentation - User Management",
        "content": """
        <h2>User Management API</h2>
        <p>This API allows you to manage user accounts programmatically.</p>
        <h3>Authentication</h3>
        <p>All API requests require authentication using API keys.</p>
        <code>Authorization: Bearer YOUR_API_KEY</code>
        <h3>Endpoints</h3>
        <h4>GET /api/users</h4>
        <p>Retrieve a list of all users.</p>
        <h4>POST /api/users</h4>
        <p>Create a new user account.</p>
        <h4>PUT /api/users/{id}</h4>
        <p>Update an existing user account.</p>
        <h4>DELETE /api/users/{id}</h4>
        <p>Delete a user account.</p>
        """
    },
    {
        "title": "Troubleshooting Common Issues",
        "content": """
        <h2>Common Issues and Solutions</h2>
        <p>This document covers frequently encountered problems and their solutions.</p>
        <h3>Login Problems</h3>
        <p><strong>Issue:</strong> Cannot log in to the system</p>
        <p><strong>Solution:</strong> Check your username and password, clear browser cache, or reset your password.</p>
        <h3>Performance Issues</h3>
        <p><strong>Issue:</strong> Application running slowly</p>
        <p><strong>Solution:</strong> Close unnecessary applications, restart your computer, or contact IT support.</p>
        <h3>Network Connectivity</h3>
        <p><strong>Issue:</strong> Cannot connect to the network</p>
        <p><strong>Solution:</strong> Check network cables, restart network adapter, or contact network administrator.</p>
        """
    },
    {
        "title": "Project Setup and Configuration",
        "content": """
        <h2>Setting Up a New Project</h2>
        <p>This guide walks you through setting up a new development project.</p>
        <h3>Initial Setup</h3>
        <ol>
            <li>Create a new project directory</li>
            <li>Initialize version control (Git)</li>
            <li>Set up virtual environment</li>
            <li>Install required dependencies</li>
        </ol>
        <h3>Configuration Files</h3>
        <p>Create the following configuration files:</p>
        <ul>
            <li><code>.env</code> - Environment variables</li>
            <li><code>requirements.txt</code> - Python dependencies</li>
            <li><code>.gitignore</code> - Git ignore rules</li>
            <li><code>README.md</code> - Project documentation</li>
        </ul>
        """
    },
    # Next 5 similar documents (variations of the above)
    {
        "title": "Account Password Recovery",
        "content": """
        <h2>Recovering Your Account Password</h2>
        <p>If you've forgotten your password, here's how to recover it:</p>
        <ol>
            <li>Navigate to the main login screen</li>
            <li>Select "Forgot your password?" option</li>
            <li>Provide your registered email address</li>
            <li>Look for recovery email in your inbox</li>
            <li>Follow the secure reset link provided</li>
            <li>Set up a new secure password</li>
        </ol>
        <p><strong>Security Tip:</strong> Use a combination of letters, numbers, and symbols. Make it at least 8 characters long.</p>
        """
    },
    {
        "title": "Application Installation Manual",
        "content": """
        <h2>How to Install Required Applications</h2>
        <p>Step-by-step guide for installing necessary software tools.</p>
        <h3>System Requirements</h3>
        <ul>
            <li>Windows 10 or newer version</li>
            <li>Admin access to the system</li>
            <li>Stable internet connection</li>
        </ul>
        <h3>Installation Process</h3>
        <ol>
            <li>Get the installer from the official source</li>
            <li>Execute installer with admin rights</li>
            <li>Complete the installation wizard</li>
            <li>Reboot system if required</li>
        </ol>
        <p>For technical difficulties, reach out to our IT help desk.</p>
        """
    },
    {
        "title": "REST API Guide - Account Management",
        "content": """
        <h2>Account Management REST API</h2>
        <p>Comprehensive guide for managing user accounts via REST API.</p>
        <h3>Security</h3>
        <p>API access requires valid authentication tokens.</p>
        <code>Authorization: Token YOUR_ACCESS_TOKEN</code>
        <h3>Available Endpoints</h3>
        <h4>GET /api/accounts</h4>
        <p>Fetch list of user accounts.</p>
        <h4>POST /api/accounts</h4>
        <p>Register a new user account.</p>
        <h4>PATCH /api/accounts/{id}</h4>
        <p>Modify existing account details.</p>
        <h4>DELETE /api/accounts/{id}</h4>
        <p>Remove user account from system.</p>
        """
    },
    {
        "title": "Problem Resolution Guide",
        "content": """
        <h2>Resolving Frequent System Problems</h2>
        <p>Quick reference for solving common technical issues.</p>
        <h3>Authentication Failures</h3>
        <p><strong>Problem:</strong> Unable to access the system</p>
        <p><strong>Resolution:</strong> Verify credentials, clear browser data, or initiate password reset.</p>
        <h3>System Performance</h3>
        <p><strong>Problem:</strong> Slow application response</p>
        <p><strong>Resolution:</strong> End unnecessary processes, restart system, or escalate to technical support.</p>
        <h3>Connection Issues</h3>
        <p><strong>Problem:</strong> Network access problems</p>
        <p><strong>Resolution:</strong> Verify connections, restart network services, or contact system administrator.</p>
        """
    },
    {
        "title": "Development Environment Setup",
        "content": """
        <h2>Configuring Your Development Environment</h2>
        <p>Complete guide for establishing a new development workspace.</p>
        <h3>Environment Preparation</h3>
        <ol>
            <li>Establish project workspace</li>
            <li>Configure source control (Git)</li>
            <li>Create isolated environment</li>
            <li>Install project dependencies</li>
        </ol>
        <h3>Essential Files</h3>
        <p>Set up these important configuration files:</p>
        <ul>
            <li><code>.env</code> - Environment configuration</li>
            <li><code>requirements.txt</code> - Package dependencies</li>
            <li><code>.gitignore</code> - Version control exclusions</li>
            <li><code>README.md</code> - Project documentation</li>
        </ul>
        """
    }
]

def create_page(title, content):
    """Create a page in Confluence"""
    try:
        # Check if page already exists
        existing_page = confluence.get_page_by_title(SPACE_KEY, title)
        if existing_page:
            print(f">> Page '{title}' already exists. Skipping...")
            return False
        
        # Create the page
        page = confluence.create_page(
            space=SPACE_KEY,
            title=title,
            body=content,
            parent_id=None,
            type='page',
            representation='storage'
        )
        print(f">> Created page: '{title}'")
        return True
    except Exception as e:
        print(f">> Error creating page '{title}': {str(e)}")
        return False

def main():
    """Main function to seed the Confluence space"""
    print(">> Starting Confluence space seeding...")
    print(f">> Target space: {SPACE_KEY}")
    print(f">> Pages to create: {len(documents)}")
    print("-" * 50)
    
    created_count = 0
    skipped_count = 0
    
    for i, doc in enumerate(documents, 1):
        print(f"[{i}/{len(documents)}] Creating: {doc['title']}")
        
        if create_page(doc['title'], doc['content']):
            created_count += 1
        else:
            skipped_count += 1
        
        # Add a small delay to avoid overwhelming the API
        time.sleep(1)
    
    print("-" * 50)
    print(">> Seeding Summary:")
    print(f">> Pages created: {created_count}")
    print(f">> Pages skipped: {skipped_count}")
    print(f">> Total processed: {len(documents)}")
    print(">> Seeding complete!")

if __name__ == "__main__":
    main()
