"""
Login page component for DocJanitor.
Handles both dev and production authentication flows.
"""
import streamlit as st
import os
from config.user_profiles import UserProfileManager

def render_dev_login():
    """Render development mode login with profile selection"""
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1>🧹 DocJanitor</h1>
            <h3>🚀 Development Mode</h3>
            <p style="color: #666;">Quick access for development</p>
        </div>
    """, unsafe_allow_html=True)
    
    profile_manager = UserProfileManager()
    profiles = profile_manager.list_profiles()
    
    if profiles:
        st.markdown("### Select Your Profile")
        
        # Create profile cards
        cols = st.columns(min(len(profiles), 3))  # Max 3 columns
        
        for i, profile_name in enumerate(profiles):
            profile = profile_manager.get_profile(profile_name)
            if profile:
                with cols[i % 3]:
                    # Create a clickable profile card
                    if st.button(
                        f"📧 {profile['email']}\n🌐 {profile['confluence_url'][:30]}...",
                        key=f"login_profile_{profile_name}",
                        use_container_width=True,
                        help=f"Login as {profile['email']}"
                    ):
                        # Load the selected profile
                        profile_data = profile_manager.get_profile_for_session_state(profile_name)
                        if profile_data:
                            profile_manager.set_active_profile(profile_name)
                            for key, value in profile_data.items():
                                setattr(st.session_state, key, value)
                            
                            # Mark as authenticated
                            st.session_state.authenticated = True
                            st.session_state.auth_method = "dev_profile"
                            st.session_state.user_email = profile['email']
                            
                            st.success(f"✅ Logged in as {profile['email']}")
                            st.rerun()
        
        st.markdown("---")
        
        # Option to create new profile
        if st.button("➕ Create New Profile", use_container_width=True):
            st.session_state.show_profile_setup = True
            st.rerun()
    
    else:
        # No profiles - show create first profile
        st.warning("No profiles found")
        st.info("Create your first profile to get started")
        
        if st.button("➕ Create First Profile", use_container_width=True):
            st.session_state.show_profile_setup = True
            st.rerun()

def render_prod_login():
    """Render production mode login with Google OAuth"""
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1>🧹 DocJanitor</h1>
            <h3>🔒 Secure Login</h3>
            <p style="color: #666;">Please authenticate to continue</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Check if Google OAuth is configured
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not google_client_id or not google_client_secret:
        st.error("🔧 Google OAuth not configured")
        st.info("""
        To enable Google OAuth, please set these environment variables:
        - `GOOGLE_CLIENT_ID`
        - `GOOGLE_CLIENT_SECRET`
        
        Get these from the Google Cloud Console.
        """)
        
        # Fallback to simple auth for now
        st.markdown("---")
        st.markdown("### Temporary Access")
        if st.button("🔓 Continue without OAuth (Development Only)", type="secondary"):
            st.session_state.authenticated = True
            st.session_state.auth_method = "temp_fallback"
            st.session_state.user_email = "temp@example.com"
            st.session_state.current_user_email = "temp@example.com"  # Set the correct session state variable
            st.rerun()
        return
    
    # Google OAuth implementation
    try:
        from streamlit_oauth import OAuth2Component
        
        # Initialize OAuth component
        oauth2 = OAuth2Component(
            client_id=google_client_id,
            client_secret=google_client_secret,
            authorize_endpoint="https://accounts.google.com/o/oauth2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            refresh_token_endpoint="https://oauth2.googleapis.com/token",
            revoke_token_endpoint="https://oauth2.googleapis.com/revoke",
        )
        
        # Create centered container for the login button
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            # Custom CSS for the container and buttons
            st.markdown("""
            <style>
                .sso-container {
                    border: 1px solid rgba(255, 255, 255, 0.2); /* Thin, transparent border */
                    background-color: transparent;
                    padding: 25px;
                    border-radius: 10px;
                    text-align: center;
                }
                /* Ensure Streamlit's button and our custom buttons are full-width */
                .sso-container .stButton button,
                .sso-container .sso-button {
                    width: 100%;
                    margin-bottom: 10px; /* Space between buttons */
                }
                .sso-button {
                    display: block;
                    padding: 10px 20px;
                    border-radius: 4px;
                    color: white;
                    border: none;
                    font-size: 14px;
                    cursor: not-allowed;
                    opacity: 0.6;
                }
            </style>
            """, unsafe_allow_html=True)

            # Start of the button container
            st.markdown('<div class="sso-container">', unsafe_allow_html=True)

            # OAuth flow - this button will be styled by the CSS above
            result = oauth2.authorize_button(
                name="🔐 Sign in with Google",
                icon="https://www.google.com/favicon.ico",
                redirect_uri="http://localhost:8502",
                scope="openid email profile",
                key="google_oauth",
                extras_params={"prompt": "consent", "access_type": "offline"},
                use_container_width=True
            )

            # Fake SSO buttons for visual appeal
            st.markdown("""
                <button class="sso-button" style="background-color: #0078d4;" disabled>
                    🏢 Sign in with Microsoft
                </button>
                <button class="sso-button" style="background-color: #ff6d01;" disabled>
                    🏢 Sign in with Azure AD
                </button>
                <button class="sso-button" style="background-color: #333;" disabled>
                    🐙 Sign in with GitHub
                </button>
            """, unsafe_allow_html=True)

            # End of the button container
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("""
                <p style="text-align: center; color: #888; font-size: 12px; margin-top: 1rem;">
                    Additional SSO options coming soon
                </p>
            """, unsafe_allow_html=True)

        if result and result.get('token'):
            # OAuth successful - extract user info
            st.session_state.authenticated = True
            st.session_state.auth_method = "google_oauth"
            st.session_state.oauth_token = result['token']

            # Get user info from token - decode JWT id_token
            user_email = None
            token_data = result.get('token', {})
            
            # Try different ways to extract email
            if 'userinfo' in token_data and 'email' in token_data['userinfo']:
                user_email = token_data['userinfo']['email']
            elif 'email' in token_data:
                user_email = token_data['email']
            elif 'id_token' in token_data:
                # Decode the JWT id_token to get email
                import base64
                import json
                try:
                    # JWT tokens have 3 parts separated by dots: header.payload.signature
                    # We need the payload (middle part)
                    id_token = token_data['id_token']
                    payload = id_token.split('.')[1]
                    # Add padding if needed for base64 decoding
                    payload += '=' * (4 - len(payload) % 4)
                    decoded_payload = base64.urlsafe_b64decode(payload)
                    jwt_data = json.loads(decoded_payload)
                    user_email = jwt_data.get('email', 'no_email_in_jwt@example.com')
                except Exception as jwt_error:
                    user_email = f'jwt_decode_error@example.com'
            else:
                user_email = 'unknown@example.com'
            
            st.session_state.user_email = user_email
            st.session_state.current_user_email = user_email  # Set the correct session state variable

            # Check if this user already has a profile
            profile_manager = UserProfileManager()
            existing_profile = None
            
            # Look for matching profile by email (case-insensitive)
            for profile_name, profile_data in profile_manager.profiles.items():
                stored_email = profile_data.get('email', '').strip().lower()
                if stored_email == user_email.strip().lower():
                    existing_profile = profile_name
                    break
            
            if existing_profile:
                # Load existing profile
                profile_data = profile_manager.get_profile_for_session_state(existing_profile)
                if profile_data:
                    profile_manager.set_active_profile(existing_profile)
                    for key, value in profile_data.items():
                        setattr(st.session_state, key, value)
                
                with col2:
                    st.success(f"✅ Welcome back! Logged in as {user_email}")
                    st.info("🔄 Loading your profile...")
            else:
                # New user - redirect to profile setup
                st.session_state.show_profile_setup = True
                st.session_state.oauth_setup_email = user_email  # Pre-fill email in form
                
                with col2:
                    st.success(f"✅ Authenticated with Google: {user_email}")
                    st.info("🔧 Please complete your profile setup to access Confluence features")
            
            st.rerun()

    except ImportError:
        st.error("streamlit-oauth not installed. Run: pip install streamlit-oauth")
    except Exception as e:
        st.error(f"OAuth error: {str(e)}")

        # Fallback option
        st.markdown("---")
        st.markdown("### Temporary Access")
        if st.button("🔓 Continue without OAuth (Development Only)", type="secondary"):
            st.session_state.authenticated = True
            st.session_state.auth_method = "temp_fallback"
            st.session_state.user_email = "temp@example.com"
            st.session_state.current_user_email = "temp@example.com"  # Set the correct session state variable
            st.rerun()

def render_login_page():
    """Main login page router"""
    # Clear any existing page state
    if 'page' in st.session_state:
        del st.session_state.page
    
    # Check mode
    dev_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
    skip_login = os.getenv('SKIP_LOGIN', 'false').lower() == 'true'
    
    # If skip_login is true, bypass everything
    if skip_login:
        st.session_state.authenticated = True
        st.session_state.auth_method = "dev_bypass"
        return True
    
    # Show appropriate login interface
    if dev_mode:
        render_dev_login()
    else:
        render_prod_login()
    
    # Handle profile setup modal if needed
    if st.session_state.get('show_profile_setup'):
        from ui.components.profile_setup import render_profile_setup_modal
        render_profile_setup_modal()
    
    return st.session_state.get('authenticated', False)

def check_authentication():
    """Check if user is authenticated and handle login flow"""
    # Check if already authenticated
    if st.session_state.get('authenticated'):
        return True
    
    # Show login page
    return render_login_page()
