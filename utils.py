import streamlit as st

# Note: The 'calculate_closing_stock' function and the old inventory DataFrame
# initialization have been removed. They are obsolete in the new transactional
# database model, where data is fetched directly from BigQuery.

def initialize_session_state():
    """Initializes session state variables for the app if they don't exist."""
    
    # For UI settings like dark mode
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    # For user authentication status
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None