# seed.py - Script to populate Confluence spaces with mock documents for duplicate testing

# Fix for SQLite3 version compatibility on cloud platforms
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

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
        },
        # SD Page 6 - Similar to SD Page 7 (third within-space pair for SD)
        {
            "title": "SD Backup and Recovery Procedures",
            "content": """
            <h2>SD System Backup and Data Recovery</h2>
            <p>Comprehensive guide for backing up and recovering SD system data and configurations.</p>
            <h3>SD Backup Strategies</h3>
            <p><strong>Daily Backups:</strong> Automated SD database backups run every night at 2 AM.</p>
            <p><strong>Weekly Backups:</strong> Full SD system configuration backup including user settings.</p>
            <p><strong>Monthly Backups:</strong> Complete SD environment backup stored off-site for disaster recovery.</p>
            <h3>SD Recovery Procedures</h3>
            <p><strong>Database Recovery:</strong> Restore SD database from the most recent backup file.</p>
            <p><strong>Configuration Recovery:</strong> Restore SD system settings from configuration backup.</p>
            <p><strong>Full System Recovery:</strong> Complete SD environment restoration from disaster recovery backup.</p>
            <h3>SD Backup Verification</h3>
            <p>All SD backups are automatically verified for integrity and completeness before storage.</p>
            """
        },
        # SD Page 7 - Similar to SD Page 6 (third within-space pair for SD)
        {
            "title": "SD Data Protection and Backup Guide",
            "content": """
            <h2>SD Data Protection and Backup Operations</h2>
            <p>Essential guide for protecting and backing up critical SD system data and settings.</p>
            <h3>SD Data Protection Methods</h3>
            <p><strong>Nightly Backups:</strong> Automated SD data backup processes execute daily at 2:00 AM.</p>
            <p><strong>Weekly Snapshots:</strong> Complete SD system configuration snapshots taken weekly.</p>
            <p><strong>Monthly Archives:</strong> Full SD environment archives created monthly for long-term storage.</p>
            <h3>SD Data Recovery Steps</h3>
            <p><strong>Database Restoration:</strong> Recover SD database from latest verified backup.</p>
            <p><strong>Settings Restoration:</strong> Restore SD configuration from system backup files.</p>
            <p><strong>Complete Recovery:</strong> Full SD system restoration from archived backups.</p>
            <h3>SD Backup Monitoring</h3>
            <p>SD backup operations are continuously monitored and validated for data integrity.</p>
            """
        },
        # SD Page 8 - Independent document (no duplicates)
        {
            "title": "SD Security Protocols and Access Control",
            "content": """
            <h2>SD Security Framework and Access Management</h2>
            <p>This document outlines the security protocols and access control mechanisms for the SD system.</p>
            <h3>Authentication Requirements</h3>
            <p>All SD users must authenticate using multi-factor authentication (MFA) including:</p>
            <ul>
                <li>Username and password combination</li>
                <li>SMS or email verification code</li>
                <li>Hardware token for privileged accounts</li>
            </ul>
            <h3>Role-Based Access Control</h3>
            <p>SD implements role-based permissions with the following levels:</p>
            <ul>
                <li><strong>SD Admin:</strong> Full system access and configuration rights</li>
                <li><strong>SD Manager:</strong> Department-level access and user management</li>
                <li><strong>SD User:</strong> Standard operational access to assigned modules</li>
                <li><strong>SD Guest:</strong> Limited read-only access to public resources</li>
            </ul>
            <h3>Security Monitoring</h3>
            <p>SD security events are logged and monitored 24/7 with automated alerting for suspicious activities.</p>
            """
        },
        # SD Page 9 - Independent document (no duplicates)
        {
            "title": "SD Performance Monitoring and Analytics",
            "content": """
            <h2>SD System Performance Monitoring</h2>
            <p>Comprehensive performance monitoring and analytics for the SD system infrastructure.</p>
            <h3>Key Performance Indicators</h3>
            <p>SD system performance is measured using the following KPIs:</p>
            <ul>
                <li>Response time for SD API calls (target: <200ms)</li>
                <li>SD database query performance (target: <50ms)</li>
                <li>SD user session duration and activity</li>
                <li>SD system uptime and availability (target: 99.9%)</li>
            </ul>
            <h3>Monitoring Tools</h3>
            <p>SD utilizes advanced monitoring tools including:</p>
            <ul>
                <li>Real-time dashboard with SD metrics visualization</li>
                <li>Automated alerting for SD performance degradation</li>
                <li>Historical trend analysis for SD capacity planning</li>
            </ul>
            <h3>Performance Optimization</h3>
            <p>Regular SD performance tuning includes database optimization, cache management, and resource allocation.</p>
            """
        },
        # SD Page 10 - Independent document (no duplicates)
        {
            "title": "SD Integration and API Documentation",
            "content": """
            <h2>SD System Integration Guide</h2>
            <p>Technical documentation for integrating external systems with the SD platform.</p>
            <h3>SD Integration Methods</h3>
            <p>SD supports multiple integration approaches:</p>
            <ul>
                <li><strong>REST API:</strong> Standard HTTP-based integration for SD services</li>
                <li><strong>WebSocket:</strong> Real-time bidirectional communication with SD</li>
                <li><strong>Message Queue:</strong> Asynchronous integration using SD message broker</li>
                <li><strong>Database Direct:</strong> Direct database integration for SD data access</li>
            </ul>
            <h3>SD API Endpoints</h3>
            <p>Core SD API endpoints include:</p>
            <code>
            GET /sd/api/v1/status - SD system health check<br>
            POST /sd/api/v1/data - Submit data to SD system<br>
            PUT /sd/api/v1/config - Update SD configuration<br>
            DELETE /sd/api/v1/cache - Clear SD system cache
            </code>
            <h3>Integration Best Practices</h3>
            <p>Follow SD integration guidelines for optimal performance, security, and reliability.</p>
            """
        },
        # SD Page 11 - Independent document (no duplicates)
        {
            "title": "SD Compliance and Audit Framework",
            "content": """
            <h2>SD Compliance and Regulatory Framework</h2>
            <p>Overview of compliance requirements and audit procedures for the SD system.</p>
            <h3>Regulatory Compliance</h3>
            <p>SD system adheres to the following regulatory standards:</p>
            <ul>
                <li>SOX compliance for financial data handling in SD</li>
                <li>GDPR compliance for personal data protection in SD</li>
                <li>HIPAA compliance for healthcare data in SD modules</li>
                <li>ISO 27001 for information security in SD infrastructure</li>
            </ul>
            <h3>Audit Requirements</h3>
            <p>Regular SD system audits include:</p>
            <ul>
                <li>Quarterly security assessments of SD components</li>
                <li>Annual penetration testing of SD infrastructure</li>
                <li>Monthly compliance reviews of SD processes</li>
                <li>Weekly backup and recovery testing for SD data</li>
            </ul>
            <h3>Documentation Standards</h3>
            <p>All SD compliance activities are documented according to regulatory requirements and best practices.</p>
            """
        },
        # SD Page 12 - Independent document (no duplicates)
        {
            "title": "SD Training and Certification Program",
            "content": """
            <h2>SD User Training and Certification</h2>
            <p>Comprehensive training program for SD system users and administrators.</p>
            <h3>Training Modules</h3>
            <p>SD training program includes the following modules:</p>
            <ul>
                <li><strong>SD Basics:</strong> Introduction to SD system navigation and core features</li>
                <li><strong>SD Advanced:</strong> Complex workflows and advanced SD functionality</li>
                <li><strong>SD Administration:</strong> System administration and configuration</li>
                <li><strong>SD Security:</strong> Security best practices and compliance requirements</li>
            </ul>
            <h3>Certification Levels</h3>
            <p>SD certification program offers multiple levels:</p>
            <ul>
                <li>SD Certified User (SCU) - Basic proficiency certification</li>
                <li>SD Certified Administrator (SCA) - Advanced administration certification</li>
                <li>SD Certified Expert (SCE) - Master-level expertise certification</li>
            </ul>
            <h3>Training Schedule</h3>
            <p>SD training sessions are conducted monthly with flexible scheduling options for all time zones.</p>
            """
        },
        # SD Page 13 - Independent document (no duplicates)
        {
            "title": "SD Change Management and Version Control",
            "content": """
            <h2>SD Change Management Process</h2>
            <p>Structured approach to managing changes and version control in the SD system.</p>
            <h3>Change Request Process</h3>
            <p>All SD system changes follow a standardized process:</p>
            <ol>
                <li>Submit SD change request with detailed requirements</li>
                <li>SD change review board evaluates impact and risks</li>
                <li>Approve or reject SD change request with justification</li>
                <li>Schedule SD change implementation during maintenance window</li>
                <li>Execute SD change with rollback plan ready</li>
                <li>Validate SD change and update documentation</li>
            </ol>
            <h3>Version Control</h3>
            <p>SD system maintains comprehensive version control:</p>
            <ul>
                <li>All SD code changes tracked in version control system</li>
                <li>SD configuration changes documented with version history</li>
                <li>SD database schema changes managed through migration scripts</li>
            </ul>
            <h3>Rollback Procedures</h3>
            <p>Emergency rollback procedures are defined for all SD system changes.</p>
            """
        },
        # SD Page 14 - Independent document (no duplicates)
        {
            "title": "SD Disaster Recovery and Business Continuity",
            "content": """
            <h2>SD Disaster Recovery Plan</h2>
            <p>Comprehensive disaster recovery and business continuity plan for the SD system.</p>
            <h3>Recovery Objectives</h3>
            <p>SD disaster recovery targets:</p>
            <ul>
                <li><strong>RTO (Recovery Time Objective):</strong> 4 hours for critical SD services</li>
                <li><strong>RPO (Recovery Point Objective):</strong> 1 hour maximum data loss for SD</li>
                <li><strong>Service Restoration:</strong> 99% of SD functionality within 8 hours</li>
            </ul>
            <h3>Recovery Procedures</h3>
            <p>SD disaster recovery involves:</p>
            <ol>
                <li>Activate SD disaster recovery team and communication plan</li>
                <li>Assess SD system damage and prioritize recovery efforts</li>
                <li>Restore SD infrastructure from backup systems</li>
                <li>Recover SD data from verified backup sources</li>
                <li>Test SD system functionality and performance</li>
                <li>Communicate SD service restoration to stakeholders</li>
            </ol>
            <h3>Business Continuity</h3>
            <p>SD business continuity measures ensure minimal operational disruption during recovery.</p>
            """
        },
        # SD Page 15 - Independent document (no duplicates)
        {
            "title": "SD Mobile Application Development Guidelines",
            "content": """
            <h2>SD Mobile App Development Standards</h2>
            <p>Guidelines and best practices for developing mobile applications that integrate with SD systems.</p>
            <h3>Development Framework</h3>
            <p>SD mobile development standards include:</p>
            <ul>
                <li><strong>Platform Support:</strong> iOS 14+ and Android 8+ for SD mobile apps</li>
                <li><strong>UI/UX Standards:</strong> Consistent SD branding and user experience</li>
                <li><strong>Performance Requirements:</strong> SD mobile apps must load within 3 seconds</li>
                <li><strong>Offline Capability:</strong> Essential SD features available without connectivity</li>
            </ul>
            <h3>SD Mobile APIs</h3>
            <p>Mobile-specific SD APIs provide:</p>
            <ul>
                <li>Optimized data transfer for mobile SD applications</li>
                <li>Push notification integration with SD system events</li>
                <li>Biometric authentication for SD mobile security</li>
                <li>Offline data synchronization with SD backend</li>
            </ul>
            <h3>Testing Requirements</h3>
            <p>SD mobile apps undergo rigorous testing on multiple devices and OS versions.</p>
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
        },
        # PERSONAL Page 6 - Similar to PERSONAL Page 7 (third within-space pair for PERSONAL)
        {
            "title": "Personal Data Backup and Sync Guide",
            "content": """
            <h2>Personal Data Backup and Synchronization</h2>
            <p>Complete guide for backing up and synchronizing personal data across devices and platforms.</p>
            <h3>Personal Backup Solutions</h3>
            <p><strong>Daily Sync:</strong> Automated personal file synchronization to cloud storage every day at 3 AM.</p>
            <p><strong>Weekly Backup:</strong> Full personal system backup including settings and applications.</p>
            <p><strong>Monthly Archive:</strong> Complete personal data archive stored on external drive for long-term safety.</p>
            <h3>Personal Data Recovery</h3>
            <p><strong>File Recovery:</strong> Restore personal files from the most recent cloud backup.</p>
            <p><strong>System Recovery:</strong> Restore personal system settings from weekly backup.</p>
            <p><strong>Complete Recovery:</strong> Full personal environment restoration from monthly archive.</p>
            <h3>Personal Backup Validation</h3>
            <p>All personal backups are automatically checked for completeness and data integrity.</p>
            """
        },
        # PERSONAL Page 7 - Similar to PERSONAL Page 6 (third within-space pair for PERSONAL)
        {
            "title": "Personal File Backup and Recovery System",
            "content": """
            <h2>Personal File Backup and Recovery Operations</h2>
            <p>Essential guide for protecting and recovering personal files and system configurations.</p>
            <h3>Personal Data Protection</h3>
            <p><strong>Nightly Sync:</strong> Automated personal data synchronization processes run daily at 3:00 AM.</p>
            <p><strong>Weekly Archives:</strong> Complete personal file archives created weekly for backup.</p>
            <p><strong>Monthly Storage:</strong> Full personal environment backups saved monthly to external storage.</p>
            <h3>Personal Recovery Methods</h3>
            <p><strong>File Restoration:</strong> Recover personal files from latest validated backup.</p>
            <p><strong>Config Restoration:</strong> Restore personal settings from system backup files.</p>
            <p><strong>Full Restoration:</strong> Complete personal system recovery from archived backups.</p>
            <h3>Personal Backup Monitoring</h3>
            <p>Personal backup operations are continuously monitored and verified for data integrity.</p>
            """
        },
        # PERSONAL Page 8 - Independent document (no duplicates)
        {
            "title": "Personal Privacy and Security Best Practices",
            "content": """
            <h2>Personal Privacy and Security Guidelines</h2>
            <p>Comprehensive guide for maintaining privacy and security in personal digital environments.</p>
            <h3>Password Management</h3>
            <p>Personal password security recommendations:</p>
            <ul>
                <li>Use unique passwords for each personal account</li>
                <li>Enable two-factor authentication on all personal services</li>
                <li>Use a reputable password manager for personal credentials</li>
                <li>Regularly update passwords for critical personal accounts</li>
            </ul>
            <h3>Personal Device Security</h3>
            <p>Secure your personal devices with:</p>
            <ul>
                <li>Strong screen locks and biometric authentication</li>
                <li>Regular operating system and app updates</li>
                <li>Encrypted storage for sensitive personal data</li>
                <li>Remote wipe capabilities for lost devices</li>
            </ul>
            <h3>Online Privacy</h3>
            <p>Protect personal privacy through careful management of digital footprint and data sharing.</p>
            """
        },
        # PERSONAL Page 9 - Independent document (no duplicates)
        {
            "title": "Personal Productivity Tools and Workflows",
            "content": """
            <h2>Personal Productivity Enhancement Guide</h2>
            <p>Tools and workflows to maximize personal productivity and efficiency in daily tasks.</p>
            <h3>Task Management</h3>
            <p>Personal task management strategies include:</p>
            <ul>
                <li>Digital task lists with priority categorization</li>
                <li>Calendar integration for deadline management</li>
                <li>Project breakdown into manageable personal milestones</li>
                <li>Regular review and adjustment of personal goals</li>
            </ul>
            <h3>Time Management</h3>
            <p>Effective personal time management techniques:</p>
            <ul>
                <li>Time blocking for focused personal work sessions</li>
                <li>Pomodoro technique for sustained concentration</li>
                <li>Elimination of personal time-wasting activities</li>
                <li>Batch processing of similar personal tasks</li>
            </ul>
            <h3>Workflow Optimization</h3>
            <p>Streamline personal workflows through automation and efficient tool selection.</p>
            """
        },
        # PERSONAL Page 10 - Independent document (no duplicates)
        {
            "title": "Personal Finance Management and Budgeting",
            "content": """
            <h2>Personal Financial Planning Guide</h2>
            <p>Comprehensive approach to managing personal finances and creating effective budgets.</p>
            <h3>Budget Creation</h3>
            <p>Personal budgeting fundamentals:</p>
            <ul>
                <li>Track all personal income sources and amounts</li>
                <li>Categorize personal expenses by priority and type</li>
                <li>Set realistic savings goals for personal objectives</li>
                <li>Monitor spending patterns and adjust personal budget accordingly</li>
            </ul>
            <h3>Financial Tools</h3>
            <p>Recommended personal finance management tools:</p>
            <ul>
                <li>Budgeting apps for tracking personal expenses</li>
                <li>Investment platforms for personal portfolio management</li>
                <li>Banking tools for personal account monitoring</li>
                <li>Tax software for personal filing preparation</li>
            </ul>
            <h3>Long-term Planning</h3>
            <p>Develop personal financial strategies for retirement, emergencies, and major life goals.</p>
            """
        },
        # PERSONAL Page 11 - Independent document (no duplicates)
        {
            "title": "Personal Health and Wellness Tracking",
            "content": """
            <h2>Personal Health and Wellness Monitoring</h2>
            <p>Guide for tracking and improving personal health and wellness through digital tools.</p>
            <h3>Health Metrics</h3>
            <p>Important personal health indicators to monitor:</p>
            <ul>
                <li>Daily physical activity and exercise duration</li>
                <li>Sleep quality and duration patterns</li>
                <li>Nutrition intake and dietary habits</li>
                <li>Stress levels and mental health indicators</li>
            </ul>
            <h3>Tracking Tools</h3>
            <p>Personal health tracking technologies:</p>
            <ul>
                <li>Fitness wearables for activity monitoring</li>
                <li>Mobile apps for nutrition and mood tracking</li>
                <li>Smart scales for weight and body composition</li>
                <li>Sleep monitors for rest quality assessment</li>
            </ul>
            <h3>Wellness Goals</h3>
            <p>Set and achieve personal wellness objectives through consistent tracking and gradual improvements.</p>
            """
        },
        # PERSONAL Page 12 - Independent document (no duplicates)
        {
            "title": "Personal Learning and Skill Development",
            "content": """
            <h2>Personal Continuous Learning Strategy</h2>
            <p>Framework for ongoing personal skill development and knowledge acquisition.</p>
            <h3>Learning Objectives</h3>
            <p>Personal learning goal categories:</p>
            <ul>
                <li>Professional skills relevant to personal career advancement</li>
                <li>Technical skills for personal project development</li>
                <li>Creative skills for personal expression and hobbies</li>
                <li>Life skills for personal growth and well-being</li>
            </ul>
            <h3>Learning Resources</h3>
            <p>Personal learning platforms and methods:</p>
            <ul>
                <li>Online courses for structured personal education</li>
                <li>Books and audiobooks for in-depth personal knowledge</li>
                <li>Workshops and seminars for hands-on personal learning</li>
                <li>Mentorship and coaching for personalized guidance</li>
            </ul>
            <h3>Progress Tracking</h3>
            <p>Monitor personal learning progress through regular assessment and skill application.</p>
            """
        },
        # PERSONAL Page 13 - Independent document (no duplicates)
        {
            "title": "Personal Home Office Setup and Ergonomics",
            "content": """
            <h2>Personal Home Office Design and Ergonomics</h2>
            <p>Complete guide for creating an efficient and healthy personal workspace at home.</p>
            <h3>Workspace Design</h3>
            <p>Personal home office design principles:</p>
            <ul>
                <li>Adequate lighting to reduce personal eye strain</li>
                <li>Proper ventilation for personal comfort and health</li>
                <li>Noise control for personal concentration and productivity</li>
                <li>Organization systems for personal efficiency and cleanliness</li>
            </ul>
            <h3>Ergonomic Setup</h3>
            <p>Personal ergonomic considerations:</p>
            <ul>
                <li>Adjustable desk and chair for personal comfort</li>
                <li>Monitor positioning to prevent personal neck strain</li>
                <li>Keyboard and mouse placement for personal wrist health</li>
                <li>Regular breaks and movement for personal physical well-being</li>
            </ul>
            <h3>Equipment Selection</h3>
            <p>Choose personal home office equipment based on specific needs and budget constraints.</p>
            """
        },
        # PERSONAL Page 14 - Independent document (no duplicates)
        {
            "title": "Personal Digital Asset Management",
            "content": """
            <h2>Personal Digital Asset Organization</h2>
            <p>Strategies for organizing and managing personal digital files, photos, and documents.</p>
            <h3>File Organization</h3>
            <p>Personal file management system:</p>
            <ul>
                <li>Consistent naming conventions for personal files</li>
                <li>Hierarchical folder structure for personal documents</li>
                <li>Regular cleanup and archiving of personal data</li>
                <li>Metadata tagging for personal file searchability</li>
            </ul>
            <h3>Digital Photos</h3>
            <p>Personal photo management strategies:</p>
            <ul>
                <li>Automatic sorting by date and event for personal photos</li>
                <li>Face recognition and tagging for personal organization</li>
                <li>Regular backup of personal photo collections</li>
                <li>Sharing and collaboration tools for personal memories</li>
            </ul>
            <h3>Cloud Storage</h3>
            <p>Optimize personal cloud storage for accessibility, security, and cost-effectiveness.</p>
            """
        },
        # PERSONAL Page 15 - Independent document (no duplicates)
        {
            "title": "Personal Vehicle Maintenance and Care",
            "content": """
            <h2>Personal Vehicle Maintenance Guide</h2>
            <p>Comprehensive guide for maintaining personal vehicles and ensuring reliable transportation.</p>
            <h3>Regular Maintenance</h3>
            <p>Personal vehicle maintenance schedule:</p>
            <ul>
                <li>Oil changes every 3,000-5,000 miles for personal vehicles</li>
                <li>Tire rotation and pressure checks for personal safety</li>
                <li>Brake inspection and fluid top-offs for personal security</li>
                <li>Battery testing and replacement for personal reliability</li>
            </ul>
            <h3>Seasonal Care</h3>
            <p>Personal vehicle seasonal maintenance:</p>
            <ul>
                <li>Winter preparation including antifreeze and tire changes</li>
                <li>Summer cooling system checks and air conditioning service</li>
                <li>Spring cleaning and detailing for personal vehicle appearance</li>
                <li>Fall preparation including heating system inspection</li>
            </ul>
            <h3>Emergency Preparedness</h3>
            <p>Maintain personal emergency kit and know basic troubleshooting for common vehicle issues.</p>
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
    print(">>   - SD Pages 6&7 are similar (within space)")
    print(">>   - PERSONAL Pages 1&2 are similar (within space)")
    print(">>   - PERSONAL Pages 4&5 are similar (within space)")
    print(">>   - PERSONAL Pages 6&7 are similar (within space)")
    print(">>   - SD Page 3 is similar to PERSONAL Page 3 (cross-space)")
    print(">>   - 14 independent documents with no duplicates")
    print(">>   - Expected: 8 duplicate pairs total (6 within-space + 1 cross-space + 1 reverse cross-space)")
    
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
                
                if scan_result['pairs_found'] >= 8:
                    print(">> 🎯 Expected 8 duplicate pairs found - Perfect!")
                elif scan_result['pairs_found'] > 0:
                    print(f">> ⚠️  Found {scan_result['pairs_found']} pairs, expected 8")
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
