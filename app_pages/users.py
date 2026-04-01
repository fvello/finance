import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth, load_auth_config, save_auth_config, add_user, RESET_KEY
import streamlit_authenticator as stauth

user = require_auth()

st.title("👥 User Management")

config = load_auth_config()

tab1, tab2 = st.tabs(["Create User", "Manage Users"])

with tab1:
    st.subheader("Create New User")
    
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_name = st.text_input("Display Name")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submitted = st.form_submit_button("Create User")
    
    if submitted:
        if not all([new_username, new_name, new_password]):
            st.error("All fields are required")
        elif new_password != confirm_password:
            st.error("Passwords do not match")
        elif new_username in config["credentials"]["usernames"]:
            st.error("Username already exists")
        else:
            add_user(new_username, new_name, new_password)
            st.success(f"User '{new_username}' created successfully!")
            st.info(f"The new user should log in and go to **Settings** to configure their People and Payment Methods before adding transactions.")

with tab2:
    st.subheader("Existing Users")
    
    usernames = list(config["credentials"]["usernames"].keys())
    
    if not usernames:
        st.info("No users found")
    else:
        selected_user = st.selectbox("Select User", usernames)
        
        if selected_user:
            user_data = config["credentials"]["usernames"][selected_user]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Username", selected_user, disabled=True, key=f"display_username_{selected_user}")
                edit_name = st.text_input("Display Name", user_data.get("name", ""), key=f"edit_name_{selected_user}")
            
            with col2:
                st.subheader("Change Password")
                new_pass = st.text_input("New Password", type="password", key=f"new_pass_{selected_user}")
                confirm_new_pass = st.text_input("Confirm New Password", type="password", key=f"confirm_new_pass_{selected_user}")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("Update User"):
                    if edit_name:
                        config["credentials"]["usernames"][selected_user]["name"] = edit_name
                    if new_pass:
                        if new_pass == confirm_new_pass:
                            hashed = stauth.Hasher.hash(new_pass)
                            config["credentials"]["usernames"][selected_user]["password"] = hashed
                        else:
                            st.error("Passwords do not match")
                            st.stop()
                    save_auth_config(config)
                    st.success("User updated successfully!")
                    st.rerun()
            
            with col_btn2:
                if selected_user != user:
                    if st.button("Delete User", type="secondary"):
                        del config["credentials"]["usernames"][selected_user]
                        save_auth_config(config)
                        st.success(f"User '{selected_user}' deleted")
                        st.rerun()
                else:
                    st.info("Cannot delete your own account")
