"""
User selector component for DocJanitor.
Renders user profile selection in the sidebar.
"""
import streamlit as st
import os
from config.user_profiles import UserProfileManager

def render_user_selector():
    """Render simplified user profile selector - now just handles background profile loading"""
    profile_manager = UserProfileManager()
    profiles = profile_manager.list_profiles()
    
    # Check if we're in dev mode with login skip
    skip_login = os.getenv('SKIP_LOGIN', 'false').lower() == 'true'
    
    if not profiles:
        # No profiles yet, return None - user will be prompted elsewhere
        if skip_login:
            # In dev mode, show a warning but don't block
            st.sidebar.warning("⚠️ No profiles found - running in dev mode")
        return None
    
    # Handle profile loading silently in the background
    current_profile_name = None
    
    # Check if we have a profile in session state
    if hasattr(st.session_state, 'current_profile_name') and st.session_state.current_profile_name:
        if st.session_state.current_profile_name in profiles:
            current_profile_name = st.session_state.current_profile_name
    
    # If no session state profile, get last used and load it silently
    if not current_profile_name:
        last_used = profile_manager.get_last_used_profile()
        if last_used and last_used['name'] in profiles:
            current_profile_name = last_used['name']
            # Auto-load the last used profile
            profile_data = profile_manager.get_profile_for_session_state(current_profile_name)
            if profile_data:
                profile_manager.set_active_profile(current_profile_name)
                for key, value in profile_data.items():
                    setattr(st.session_state, key, value)
    
    return current_profile_name

def check_user_profile_required():
    """Check if user needs to set up a profile and show appropriate message"""
    profile_manager = UserProfileManager()
    profiles = profile_manager.list_profiles()
    
    # Skip checks in dev mode
    skip_login = os.getenv('SKIP_LOGIN', 'false').lower() == 'true'
    if skip_login:
        return True
    
    # If authenticated but no profiles, allow creation in Settings
    if not profiles:
        st.info("👈 Please create a user profile in Settings to get started")
        return True  # Allow access to create profile
    
    # Check if we have valid session state
    required_fields = ['current_user_email', 'confluence_url', 'api_token']
    missing_fields = [field for field in required_fields if not getattr(st.session_state, field, None)]
    
    if missing_fields:
        st.warning(f"👈 Please select a user profile in Settings to continue")
        return True  # Allow access to select profile
    
    return True
