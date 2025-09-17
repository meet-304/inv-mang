import streamlit as st
from utils import initialize_session_state
from styles import custom_css
from dashboard import show_dashboard
from add_record import show_add_record
from view_records import show_view_records
from analytics import show_analytics
from edit_record import show_edit_record
from register import main as register_main
from admin_panel import show_admin_panel

# Initialize session state variables
initialize_session_state()

st.set_page_config(page_title="Inventory App", layout="wide")
custom_css()

# --- Main App Router ---

# Check if the user is logged in
if 'user' not in st.session_state or st.session_state['user'] is None:
    register_main()
    
else:
    st.sidebar.markdown(f"## Welcome, {st.session_state['user']}! <small>({st.session_state.get('user_role')})</small>", unsafe_allow_html=True)
    
    # Role-Based Navigation
    page_options = []
    user_role = st.session_state.get('user_role')

    # --- MODIFIED LINE ---

    if user_role == 'Sadmin':
        page_options = [
            "Dashboard", "Add Transaction", "View Transactions", "Correction Transaction", "Analytics", "Admin Panel"
        ]
    elif user_role == 'admin':
        page_options = [
            "Dashboard", "Add Transaction", "View Transactions", "Correction Transaction", "Analytics"
        ]
    else:
        page_options = ["Add Transaction", "View Transactions"]

    page = st.sidebar.radio("Go to", page_options)

    # Add a separator before the logout button for better UI
    st.sidebar.write("---")
    
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Add Transaction":
        show_add_record()
    elif page == "Correction Transaction":
        show_edit_record()
    elif page == "View Transactions":
        show_view_records()
    elif page == "Analytics":
        show_analytics()
    elif page == "Admin Panel":
        show_admin_panel()