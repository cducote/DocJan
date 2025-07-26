"""
Settings page for DocJanitor.
"""
import streamlit as st
from models.database import scan_for_duplicates
from confluence.api import load_documents_from_spaces, get_available_spaces
from config.user_profiles import UserProfileManager
from ui.components.profile_setup import render_profile_setup_modal

def render_settings():
    """
    Render the settings page
    """
    st.title("⚙️ Settings")
    st.markdown("Configure DocJanitor settings and perform maintenance operations.")
    
    # User Profile Management Section
    st.markdown("## 👤 User Profile Management")
    
    profile_manager = UserProfileManager()
    profiles = profile_manager.list_profiles()
    
    if profiles:
        # Show current active profile
        current_profile = None
        if hasattr(st.session_state, 'current_profile_name') and st.session_state.current_profile_name:
            current_profile = profile_manager.get_profile(st.session_state.current_profile_name)
        
        if current_profile:
            st.success(f"✅ Active Profile: **{current_profile['email']}**")
            st.caption(f"🌐 {current_profile['confluence_url']}")
        else:
            st.warning("No active profile selected")
        
        # Profile management actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("➕ Create New Profile", use_container_width=True, key="settings_new_profile"):
                st.session_state.show_profile_setup = True
        
        with col2:
            if st.button("✏️ Edit Current Profile", use_container_width=True, key="settings_edit_profile", disabled=not current_profile):
                if current_profile:
                    st.session_state.edit_profile = st.session_state.current_profile_name
                    st.session_state.show_profile_setup = True
        
        with col3:
            if st.button("🔄 Switch Profile", use_container_width=True, key="settings_switch_profile"):
                # Show profile selection
                selected_profile = st.selectbox(
                    "Choose a profile:",
                    options=profiles,
                    key="settings_profile_selector"
                )
                
                if st.button("Apply Selection", key="settings_apply_profile"):
                    profile_data = profile_manager.get_profile_for_session_state(selected_profile)
                    if profile_data:
                        profile_manager.set_active_profile(selected_profile)
                        for key, value in profile_data.items():
                            setattr(st.session_state, key, value)
                        st.success(f"✅ Switched to profile: {selected_profile}")
        
        # List all profiles with management options
        st.markdown("### All Profiles")
        for profile_name in profiles:
            profile = profile_manager.get_profile(profile_name)
            if profile:
                with st.expander(f"📧 {profile['email']} ({'Active' if profile_name == st.session_state.get('current_profile_name') else 'Inactive'})", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Email:** {profile['email']}")
                        st.write(f"**Confluence URL:** {profile['confluence_url']}")
                        st.write(f"**Created:** {profile.get('created_at', 'Unknown')}")
                        st.write(f"**Last Used:** {profile.get('last_used', 'Never')}")
                        
                        # Show preferences if available
                        if profile.get('preferences'):
                            prefs = profile['preferences']
                            st.write(f"**Default Similarity:** {prefs.get('default_similarity', 0.65)}")
                            st.write(f"**Auto Load Spaces:** {'Yes' if prefs.get('auto_load_spaces') else 'No'}")
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"settings_delete_{profile_name}", help="Delete this profile"):
                            if st.session_state.get(f'confirm_delete_{profile_name}'):
                                # Confirmed deletion
                                success = profile_manager.delete_profile(profile_name)
                                if success:
                                    # Clear session state if deleting active profile
                                    if profile_name == st.session_state.get('current_profile_name'):
                                        for key in ['current_profile_name', 'current_user_email', 'confluence_url', 'api_token']:
                                            if hasattr(st.session_state, key):
                                                delattr(st.session_state, key)
                                    st.success(f"Profile '{profile_name}' deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete profile")
                            else:
                                # Ask for confirmation
                                st.session_state[f'confirm_delete_{profile_name}'] = True
                                st.warning("Click again to confirm")
    else:
        st.info("No user profiles found. Create your first profile to get started.")
        if st.button("➕ Create First Profile", use_container_width=True, key="settings_create_first"):
            st.session_state.show_profile_setup = True
    
    # Render profile setup modal if needed
    if st.session_state.get('show_profile_setup'):
        render_profile_setup_modal()
    
    st.markdown("---")
    
    # Duplicate detection settings
    st.markdown("## 🔍 Duplicate Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.50,
            max_value=0.95,
            value=0.65,
            step=0.05,
            help="Documents with similarity above this threshold will be considered potential duplicates"
        )
    
    with col2:
        st.markdown("**Current Threshold:** 65%")
        st.markdown("- **50-60%:** Very loose matching (many false positives)")
        st.markdown("- **65-75%:** Balanced matching (recommended)")
        st.markdown("- **80-95%:** Strict matching (may miss some duplicates)")
    
    # Manual duplicate scan
    if st.button("🔍 Run Duplicate Scan", use_container_width=True, key="settings_run_scan"):
        with st.spinner("Scanning for duplicates..."):
            result = scan_for_duplicates(similarity_threshold=similarity_threshold, update_existing=True)
            
            if result['success']:
                st.success(f"✅ {result['message']}")
                if result.get('pairs_found', 0) > 0:
                    st.info(f"Found {result['pairs_found']} potential duplicate pairs. Go to the Duplicates page to review them.")
            else:
                st.error(f"❌ Scan failed: {result['message']}")
    
    st.markdown("---")
    
    # Space management
    st.markdown("## 🏢 Space Management")
    
    # Show currently selected spaces
    selected_spaces = st.session_state.get('selected_spaces', [])
    if selected_spaces:
        st.markdown(f"**Currently monitoring {len(selected_spaces)} space(s):** {', '.join(selected_spaces)}")
    else:
        st.warning("No spaces currently selected for monitoring.")
    
    # Load documents from spaces
    st.markdown("### Load Documents from Confluence")
    
    available_spaces = st.session_state.get('available_spaces', [])
    if not available_spaces:
        if st.button("🔄 Load Available Spaces", key="settings_load_spaces"):
            with st.spinner("Loading available spaces..."):
                spaces = get_available_spaces()
                st.session_state.available_spaces = spaces
                st.rerun()
    else:
        space_options = [(space['key'], f"{space['name']} ({space['key']})") for space in available_spaces]
        
        selected_space_keys = st.multiselect(
            "Select spaces to load documents from:",
            options=[key for key, _ in space_options],
            format_func=lambda key: next(label for k, label in space_options if k == key)
        )
        
        col1, col2 = st.columns(2)
        with col1:
            docs_per_space = st.number_input(
                "Documents per space",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                help="Maximum number of documents to load from each space"
            )
        
        with col2:
            if st.button("📥 Load Documents", disabled=not selected_space_keys, key="settings_load_docs"):
                with st.spinner(f"Loading documents from {len(selected_space_keys)} space(s)..."):
                    result = load_documents_from_spaces(selected_space_keys, docs_per_space)
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        # Auto-run duplicate scan after loading
                        if result.get('total_loaded', 0) > 0:
                            st.info("Running automatic duplicate scan on newly loaded documents...")
                            scan_result = scan_for_duplicates(similarity_threshold=similarity_threshold)
                            if scan_result['success'] and scan_result.get('pairs_found', 0) > 0:
                                st.info(f"Found {scan_result['pairs_found']} potential duplicates after loading.")
                    else:
                        st.error(f"❌ {result['message']}")
                        if result.get('errors'):
                            with st.expander("View Errors"):
                                for error in result['errors']:
                                    st.text(error)
    
    st.markdown("---")
    
    # Database maintenance
    st.markdown("## 🗄️ Database Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ChromaDB Status")
        from models.database import get_document_database
        db = get_document_database()
        
        try:
            all_docs = db.get()
            doc_count = len(all_docs['documents']) if all_docs['documents'] else 0
            st.metric("Total Documents", doc_count)
        except Exception as e:
            st.error(f"Database error: {str(e)}")
    
    with col2:
        st.markdown("### Quick Actions")
        
        if st.button("🧹 Clean Duplicate DB Entries", key="settings_clean_db"):
            from models.database import cleanup_duplicate_database_entries
            with st.spinner("Cleaning up duplicate database entries..."):
                success, message = cleanup_duplicate_database_entries()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
        
        if st.button("🔄 Refresh Space List", key="settings_refresh_spaces"):
            with st.spinner("Refreshing available spaces..."):
                spaces = get_available_spaces()
                st.session_state.available_spaces = spaces
                st.success(f"✅ Loaded {len(spaces)} available spaces")
                st.rerun()
    
    st.markdown("---")
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        st.markdown("### Debug Information")
        
        # Show session state for debugging
        if st.checkbox("Show Session State"):
            st.json({
                "page": st.session_state.get("page"),
                "selected_spaces": st.session_state.get("selected_spaces"),
                "available_spaces_count": len(st.session_state.get("available_spaces", [])),
                "merge_docs": "Set" if st.session_state.get("merge_docs") else "None",
                "merged_content": "Set" if st.session_state.get("merged_content") else "None"
            })
        
        # Reset session state
        if st.button("🔄 Reset Session State", key="settings_reset_session"):
            # Keep only essential state
            essential_keys = ['page', 'selected_spaces', 'available_spaces']
            keys_to_remove = [key for key in st.session_state.keys() if key not in essential_keys]
            
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.success("Session state reset!")
            st.rerun()
    
    # Dangerous Operations
    st.markdown("---")
    st.markdown("## ⚠️ Dangerous Operations")
    st.warning("These operations are irreversible and will affect your Confluence space and database.")
    
    # Initialize reset confirmation state
    if 'reset_confirmation' not in st.session_state:
        st.session_state.reset_confirmation = False
    
    # Reset confirmation workflow
    if not st.session_state.reset_confirmation:
        if st.button("🔥 Reset Everything", use_container_width=True, help="Delete ALL pages and reset database", key="settings_reset_everything"):
            st.session_state.reset_confirmation = True
            st.rerun()
    else:
        st.warning("⚠️ **WARNING**: This will permanently delete ALL pages in the Confluence space and reset the database!")
        st.markdown("This action is **irreversible**. Are you sure?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Reset", use_container_width=True, type="primary", key="settings_confirm_reset"):
                # Run the reset
                with st.spinner("🔥 Resetting everything..."):
                    try:
                        # Import and run the reset function with error handling
                        import subprocess
                        import sys
                        import os
                        
                        # Run reset.py as a subprocess to avoid encoding issues
                        result = subprocess.run(
                            [sys.executable, "reset.py"],
                            cwd=os.getcwd(),
                            capture_output=True,
                            text=True,
                            input="SD\nyes\n",  # Auto-confirm with default space
                            timeout=300  # 5 minute timeout
                        )
                        
                        if result.returncode == 0:
                            st.session_state.reset_result = {
                                'success': True,
                                'message': 'Reset completed successfully!',
                                'details': result.stdout
                            }
                        else:
                            st.session_state.reset_result = {
                                'success': False,
                                'error': f"Reset process failed with return code {result.returncode}",
                                'details': result.stderr
                            }
                        
                        st.session_state.reset_confirmation = False
                        st.rerun()
                        
                    except subprocess.TimeoutExpired:
                        st.error("Reset failed: Operation timed out after 5 minutes")
                        st.session_state.reset_confirmation = False
                    except Exception as e:
                        st.error(f"Reset failed: {str(e)}")
                        st.session_state.reset_confirmation = False
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True, key="settings_cancel_reset"):
                st.session_state.reset_confirmation = False
                st.rerun()
    
    # Show reset results if available
    if 'reset_result' in st.session_state and st.session_state.reset_result:
        st.markdown("### Reset Results")
        if st.session_state.reset_result.get('success'):
            st.success("✅ Reset completed successfully!")
            if 'details' in st.session_state.reset_result:
                with st.expander("View Details"):
                    st.text(st.session_state.reset_result['details'])
        else:
            st.error("❌ Reset failed!")
            if 'error' in st.session_state.reset_result:
                st.error(st.session_state.reset_result['error'])
            if 'details' in st.session_state.reset_result:
                with st.expander("View Error Details"):
                    st.text(st.session_state.reset_result['details'])
        
        if st.button("Clear Results", key="settings_clear_reset_results"):
            if 'reset_result' in st.session_state:
                del st.session_state.reset_result
            st.rerun()
    
    # Navigation
    st.markdown("---")
    if st.button("← Back to Dashboard", key="settings_back_to_dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
