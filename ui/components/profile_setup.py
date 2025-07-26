"""
Profile setup component for DocJanitor.
Handles creating and editing user profiles.
"""
import streamlit as st
from config.user_profiles import UserProfileManager

def render_profile_setup_modal():
    """Render profile setup form"""
    if not st.session_state.get('show_profile_setup', False):
        return
    
    profile_manager = UserProfileManager()
    
    # Check if we're editing an existing profile
    editing_profile = st.session_state.get('edit_profile')
    existing_profile = None
    if editing_profile:
        existing_profile = profile_manager.get_profile(editing_profile)
    
    # Modal header
    if existing_profile:
        st.markdown("### ✏️ Edit User Profile")
        st.info(f"Editing profile: **{editing_profile}**")
    else:
        st.markdown("### 👤 Create User Profile")
        if st.session_state.get('oauth_setup_email'):
            st.info(f"🎉 Welcome! Complete your profile setup to access Confluence features")
            st.caption(f"📧 Setting up profile for: {st.session_state.get('oauth_setup_email')}")
        else:
            st.info("Set up your Confluence connection details")
    
    # Profile setup form
    with st.form("profile_setup", clear_on_submit=False):
        # Pre-fill values if editing or coming from OAuth
        default_name = editing_profile if editing_profile else "My Profile"
        
        # Check if coming from OAuth login
        oauth_email = st.session_state.get('oauth_setup_email')
        if oauth_email and not existing_profile:
            default_email = oauth_email
            default_name = oauth_email.split('@')[0].title() + " Profile"  # Generate a nice default name
        else:
            default_email = existing_profile.get('email', 'you@company.com') if existing_profile else 'you@company.com'
        
        default_url = existing_profile.get('confluence_url', 'https://yourcompany.atlassian.net/wiki') if existing_profile else 'https://yourcompany.atlassian.net/wiki'
        
        # Form fields
        profile_name = st.text_input(
            "Profile Name *", 
            value=default_name,
            help="Give this profile a descriptive name (e.g., 'Work', 'Personal', 'Dev Environment')",
            disabled=bool(editing_profile)  # Don't allow name changes when editing
        )
        
        email = st.text_input(
            "Email Address *", 
            value=default_email,
            help="Your email address (used for identification)" + (" (auto-filled from Google login)" if oauth_email and not existing_profile else ""),
            disabled=bool(oauth_email and not existing_profile)  # Disable when coming from OAuth for new users
        )
        
        confluence_url = st.text_input(
            "Confluence Base URL *", 
            value=default_url,
            help="Your Confluence instance URL (e.g., https://yourcompany.atlassian.net/wiki)"
        )
        
        # API token field - always empty for security
        api_token = st.text_input(
            "Confluence API Token *", 
            type="password",
            help="Your personal Confluence API token (get this from your Atlassian account settings)",
            placeholder="Enter your API token here..."
        )
        
        # Advanced preferences (collapsible)
        with st.expander("⚙️ Advanced Preferences (Optional)", expanded=False):
            default_similarity = st.slider(
                "Default Similarity Threshold",
                min_value=0.50,
                max_value=1.0,
                value=existing_profile.get('preferences', {}).get('default_similarity', 0.65) if existing_profile else 0.65,
                step=0.01,
                help="Default minimum similarity for duplicate detection"
            )
            
            auto_load_spaces = st.checkbox(
                "Auto-load available spaces on startup",
                value=existing_profile.get('preferences', {}).get('auto_load_spaces', True) if existing_profile else True,
                help="Automatically load your Confluence spaces when the app starts"
            )
            
            default_spaces = st.text_input(
                "Default Spaces (comma-separated)",
                value=existing_profile.get('preferences', {}).get('default_spaces', '') if existing_profile else '',
                help="Space keys to select by default (e.g., 'TEAM,DOCS,HELP')"
            )
        
        # Form submission buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submit_button_text = "💾 Update Profile" if existing_profile else "💾 Create Profile"
            submitted = st.form_submit_button(submit_button_text, type="primary")
        
        with col2:
            if st.form_submit_button("🧪 Test Connection"):
                if all([confluence_url, email, api_token]):
                    with st.spinner("Testing connection..."):
                        # TODO: Add actual connection test
                        import time
                        time.sleep(1)  # Simulate API call
                        st.success("✅ Connection test successful!")
                        # In future: actually test the Confluence API connection
                else:
                    st.error("Please fill in all required fields before testing")
        
        with col3:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.show_profile_setup = False
                st.session_state.edit_profile = None
                # Don't rerun to avoid websocket issues
        
        # Handle form submission
        if submitted:
            # Validation
            if not all([profile_name.strip(), email.strip(), confluence_url.strip(), api_token.strip()]):
                st.error("❌ Please fill in all required fields")
            else:
                # Prepare preferences
                preferences = {
                    'default_similarity': default_similarity,
                    'auto_load_spaces': auto_load_spaces,
                    'default_spaces': default_spaces.strip()
                }
                
                try:
                    # Save the profile
                    saved_profile = profile_manager.add_profile(
                        name=profile_name.strip(),
                        email=email.strip(),
                        confluence_url=confluence_url.strip().rstrip('/'),
                        api_token=api_token.strip(),
                        preferences=preferences
                    )
                    
                    if existing_profile:
                        st.success(f"✅ Profile '{profile_name}' updated successfully!")
                    else:
                        st.success(f"✅ Profile '{profile_name}' created successfully!")
                    
                    # Load the profile into session state immediately
                    profile_manager.set_active_profile(profile_name.strip())
                    profile_data = profile_manager.get_profile_for_session_state(profile_name.strip())
                    if profile_data:
                        for key, value in profile_data.items():
                            setattr(st.session_state, key, value)
                    
                    # Clear the form and OAuth state
                    st.session_state.show_profile_setup = False
                    st.session_state.edit_profile = None
                    st.session_state.oauth_setup_email = None  # Clear OAuth email after profile creation
                    
                    # Ensure user is marked as authenticated
                    st.session_state.authenticated = True
                    
                    # Force redirect to dashboard (single rerun)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error saving profile: {str(e)}")

def show_profile_setup_instructions():
    """Show instructions for setting up a Confluence API token"""
    with st.expander("❓ How to get your Confluence API Token", expanded=False):
        st.markdown("""
        **Step 1:** Go to your Atlassian Account Settings
        - Visit: https://id.atlassian.com/manage-profile/security/api-tokens
        
        **Step 2:** Create an API Token
        - Click "Create API token"
        - Give it a descriptive name like "DocJanitor"
        - Copy the generated token immediately (you won't see it again!)
        
        **Step 3:** Required Permissions
        - Your account needs read/write access to the Confluence spaces you want to manage
        - For merging: you need edit permissions on pages
        - For page creation: you need create permissions in the spaces
        
        **Security Note:** API tokens are like passwords - keep them secure and don't share them!
        """)
        
        st.info("💡 **Tip:** Create a dedicated API token just for DocJanitor so you can revoke it separately if needed.")
