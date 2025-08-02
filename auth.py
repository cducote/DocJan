"""
Simple authentication module for Concatly sandbox
"""
import streamlit as st
import hashlib

# Hardcoded credentials for sandbox (change these!)
SANDBOX_USERS = {
    "demo": "password123",  # username: password
    "tester": "test456",
    "admin": "admin789"
}

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    """Check if username/password combination is valid"""
    if username in SANDBOX_USERS:
        return SANDBOX_USERS[username] == password
    return False

def login_form():
    """Display login form and handle authentication"""
    st.title("🔐 Concatly Sandbox Access")
    st.markdown("---")
    
    # Create login form
    with st.form("login_form"):
        st.subheader("Please enter your credentials")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    

def logout():
    """Handle user logout"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

def require_auth():
    """Decorator function to require authentication for pages"""
    if not st.session_state.get('authenticated', False):
        login_form()
        return False
    return True

def show_auth_status():
    """Show current authentication status in sidebar"""
    if st.session_state.get('authenticated', False):
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Logged in as:** {st.session_state.get('username', 'Unknown')}")
            if st.button("Logout", key="logout_btn"):
                logout()
