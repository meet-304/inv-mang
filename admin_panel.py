# admin_panel.py

import streamlit as st
import pandas as pd
from bq_database import get_all_users, update_user_role, delete_user, update_user_restriction

def show_admin_panel():
    st.title("👑 Admin Panel")
    st.subheader("Manage User Roles & Permissions")

    logged_in_user_role = st.session_state.get('user_role')
    logged_in_user_id = st.session_state.get('user_id')

    try:
        users_df = get_all_users()
        users_df = users_df[users_df['user_id'] != logged_in_user_id].copy()
    except Exception as e:
        st.error(f"Failed to load users: {e}")
        return

    if logged_in_user_role == 'admin':
        users_df = users_df[users_df['user_role'] != 'Sadmin'].copy()

    if users_df.empty:
        st.info("No other users found to manage.")
        return

    for index, user in users_df.iterrows():
        st.write("---")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
            st.write(f"**Username:** {user['username']}")
            st.caption(f"Email: {user['email']}")

        with col2:
            if user['user_role'] == 'Sadmin':
                st.markdown("`Super Admin`")
                st.caption("Cannot be modified.")
            else:
                role_options = ['user', 'admin']
                current_role_index = role_options.index(user['user_role'])
                new_role = st.selectbox("Change Role", options=role_options, index=current_role_index, key=f"role_{user['user_id']}")
        
        with col3:
            # --- MODIFIED: Replaced selectbox with multiselect ---
            restriction_options = ['Production', 'Purchase', 'Sales', 'Breakage']
            
            # Parse the user's current restrictions from the DB string
            current_restrictions = []
            if pd.notna(user['allowed_transaction']) and user['allowed_transaction'] != 'all':
                current_restrictions = user['allowed_transaction'].split(',')

            new_restrictions = st.multiselect(
                "Allowed Transactions (leave empty for all)", 
                options=restriction_options, 
                default=current_restrictions, 
                key=f"restriction_{user['user_id']}"
            )

        with col4:
            st.write("")
            st.write("")
            if st.button("Save", key=f"save_{user['user_id']}"):
                try:
                    if user['user_role'] != 'Sadmin':
                        update_user_role(user['user_id'], new_role)
                    # Pass the list of new restrictions to the updated function
                    update_user_restriction(user['user_id'], new_restrictions)
                    st.success(f"Updated settings for {user['username']}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")

            if logged_in_user_role == 'Sadmin' and user['user_role'] != 'Sadmin':
                if st.button("Delete", type="primary", key=f"delete_{user['user_id']}"):
                    try:
                        delete_user(user['user_id'])
                        st.warning(f"Deleted user {user['username']}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")