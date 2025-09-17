import streamlit as st
from bq_database import email_exists, username_exists, create_user, authenticate, update_user_password

def forgot_password_ui():
    st.subheader("🔒 Forgot Password")
    with st.form("forgot_password_form", clear_on_submit=True):
        email = st.text_input("Enter your registered email", placeholder="your.email@example.com")
        new_password = st.text_input("New password", type="password", placeholder="At least 6 characters")
        confirm_password = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Reset Password")
        if submitted:
            if not email_exists(email):
                st.error("No account found with this email.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password should be at least 6 characters.")
            else:
                update_user_password(email, new_password)
                st.success("Password has been reset. You can now login.")

def register_ui():
    st.subheader("🆕 Create a new account")
    with st.form("register_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        username = col1.text_input("Username", placeholder="Choose a unique username")
        email = col2.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters")
        submitted = st.form_submit_button("Register")
        if submitted:
            if username_exists(username):
                st.error("Username already taken.")
            elif email_exists(email):
                st.error("Email already registered.")
            elif len(password) < 6:
                st.error("Password should be at least 6 characters.")
            else:
                create_user(username, email, password)
                st.success("Registration successful! Please login.")

def login_ui():
    st.subheader("🔐 Login to your account")
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            valid, username, user_id, role, allowed_transaction = authenticate(email, password)
            if valid:
                st.success(f"Welcome, {username}!")
                st.session_state['user'] = username
                st.session_state['user_id'] = user_id
                st.session_state['user_role'] = role
                st.session_state['allowed_transaction'] = allowed_transaction
                st.rerun()
            else:
                st.error("Invalid credentials.")

def main():
    st.title("Inventory Management App")
    st.markdown(
        """
        <style>
        .stRadio > div {flex-direction: row; gap: 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    form_type = st.radio("Select action", ("Login", "Register", "Forgot Password"), index=0, horizontal=True)
    st.write("---")
    if form_type == "Register":
        register_ui()
    elif form_type == "Login":
        login_ui()
    elif form_type == "Forgot Password":
        forgot_password_ui()

if __name__ == "__main__":
    main()