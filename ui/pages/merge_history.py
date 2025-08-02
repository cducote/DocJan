"""
Merge history page for Concatly.
"""
import streamlit as st
from models.database import get_recent_merges
from confluence.api import undo_merge_operation
from utils.helpers import format_timestamp_to_est

def render_merge_history():
    """
    Render the merge history page
    """
    st.title("📜 Merge History")
    st.markdown("View and manage your document merge operations.")
    
    # Get recent merge operations
    merge_operations = get_recent_merges(limit=50)
    
    if not merge_operations:
        st.info("No merge operations found.")
        if st.button("← Back to Dashboard", key="merge_history_no_ops_back"):
            st.session_state.page = 'dashboard'
            st.rerun()
        return
    
    # Display merge operations
    st.markdown(f"### Recent Merge Operations ({len(merge_operations)})")
    
    for i, operation in enumerate(merge_operations):
        # Determine status styling
        status = operation.get('status', 'completed')
        if status == 'completed':
            status_emoji = "✅"
            status_color = "green"
        elif status == 'undone':
            status_emoji = "↩️"
            status_color = "orange"
        else:
            status_emoji = "❓"
            status_color = "gray"
        
        # Create card for each operation
        with st.container(border=True):
            # Header with status and timestamp
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {status_emoji} Merge Operation #{i+1}")
                timestamp = operation.get('timestamp', '')
                if timestamp:
                    formatted_time = format_timestamp_to_est(timestamp)
                    st.markdown(f"**Performed:** {formatted_time}")
            
            with col2:
                st.markdown(f"**Status:** :{status_color}[{status.title()}]")
            
            # Merge details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Kept Document")
                kept_title = operation.get('kept_title', 'Unknown')
                kept_url = operation.get('kept_url', '')
                if kept_url:
                    st.markdown(f"**Title:** [{kept_title}]({kept_url})")
                else:
                    st.markdown(f"**Title:** {kept_title}")
                st.markdown(f"**Page ID:** {operation.get('kept_page_id', 'Unknown')}")
            
            with col2:
                st.markdown("#### Deleted Document")
                deleted_title = operation.get('deleted_title', 'Unknown')
                deleted_url = operation.get('deleted_url', '')
                if deleted_url:
                    st.markdown(f"**Title:** [{deleted_title}]({deleted_url})")
                else:
                    st.markdown(f"**Title:** {deleted_title}")
                st.markdown(f"**Page ID:** {operation.get('deleted_page_id', 'Unknown')}")
            
            # Actions
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if status == 'completed':
                    if st.button("↩️ Undo Merge", key=f"undo_{i}"):
                        st.session_state.selected_undo_operation = operation
                        st.session_state.show_undo_confirmation = True
                        st.rerun()
            
            with col2:
                if kept_url:
                    st.markdown(f"[🔗 View Kept Page]({kept_url})")
            
            # Show undo confirmation dialog
            if (st.session_state.get('show_undo_confirmation', False) and 
                st.session_state.get('selected_undo_operation', {}).get('id') == operation.get('id')):
                
                st.markdown("---")
                st.warning("⚠️ **Confirm Undo Operation**")
                st.markdown("This will:")
                st.markdown("- Restore the kept page to its pre-merge version")
                st.markdown("- Restore the deleted page from Confluence trash")
                st.markdown("- Update the ChromaDB to reflect the restored state")
                st.markdown("- Automatically scan for duplicates")
                
                col_a, col_b, col_c = st.columns([1, 1, 2])
                
                with col_a:
                    if st.button("❌ Cancel", key=f"cancel_undo_{i}"):
                        st.session_state.show_undo_confirmation = False
                        st.session_state.selected_undo_operation = None
                        st.rerun()
                
                with col_b:
                    if st.button("✅ Confirm Undo", key=f"confirm_undo_{i}", type="primary"):
                        # Perform the undo operation
                        with st.spinner("Undoing merge operation..."):
                            undo_success, undo_message = undo_merge_operation(operation.get('id'))
                            
                            if undo_success:
                                st.success(undo_message)
                                st.session_state.show_undo_confirmation = False
                                st.session_state.selected_undo_operation = None
                                # Refresh the page to show updated status
                                st.rerun()
                            else:
                                st.error(f"Failed to undo merge: {undo_message}")
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("← Back to Dashboard", key="merge_history_main_back"):
            st.session_state.page = 'dashboard'
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh History", key="merge_history_refresh"):
            st.rerun()
    
    with col3:
        st.markdown("**Tip:** Undo operations restore both documents and automatically scan for duplicates.")
