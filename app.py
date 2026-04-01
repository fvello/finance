import streamlit as st
import os
from auth import get_authenticator, get_current_user, reset_user_password, create_user_with_key

st.set_page_config(page_title="Finance Tracker", page_icon="💰")

authenticator, config = get_authenticator()
authenticator.login(location="main")

if not st.session_state.get("authentication_status"):
    with st.expander("Create Account"):
        new_username = st.text_input("Username", key="create_username")
        new_name = st.text_input("Display Name", key="create_name")
        new_password = st.text_input("Password", type="password", key="create_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="create_confirm_password")
        create_key = st.text_input("Key (contact admin)", type="password", key="create_key")
        
        if st.button("Create Account"):
            if not all([new_username, new_name, new_password, create_key]):
                st.error("All fields are required")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = create_user_with_key(new_username, new_name, new_password, create_key)
                if success:
                    st.success(message + " You can now login.")
                else:
                    st.error(message)
    
    with st.expander("Forgot Password?"):
        reset_username = st.text_input("Username", key="reset_username")
        reset_key = st.text_input("Key (contact admin)", type="password", key="reset_key")
        new_password = st.text_input("New Password", type="password", key="new_password_reset")
        
        if st.button("Reset Password"):
            if reset_user_password(reset_username, new_password, reset_key):
                st.success("Password reset! You can now login.")
            else:
                st.error("Invalid username or key")

if st.session_state.get("authentication_status"):
    authenticator.logout(location="sidebar")
    st.sidebar.write(f"Welcome, **{st.session_state.get('name')}**")
    
    pages = [
        st.Page("app_pages/balance.py", title="Home", icon="🏠"),
        st.Page("app_pages/savings.py", title="Savings", icon="🪙"),
        st.Page("app_pages/input.py", title="Input", icon="📝"),
        st.Page("app_pages/expected_income.py", title="Expected Income", icon="💰"),
        st.Page("app_pages/expected_payment.py", title="Expected Payments", icon="💸"),
        st.Page("app_pages/import.py", title="Import", icon="📁"),
        st.Page("app_pages/invoice.py", title="Invoice", icon="💳"),
        st.Page("app_pages/analytics.py", title="Analytics", icon="📈"),
        st.Page("app_pages/database.py", title="Database", icon="📊"),
        st.Page("app_pages/users.py", title="Users", icon="👥"),
        st.Page("app_pages/settings.py", title="Settings", icon="⚙️"),
    ]
    
    pg = st.navigation(pages, position="sidebar", expanded=True)
    pg.run()
    
elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect")
    
elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your username and password")
