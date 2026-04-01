import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

AUTH_CONFIG_PATH = "auth.yaml"
RESET_KEY = "eusouumaputinhacomalzheimer"

def load_auth_config():
    if not os.path.exists(AUTH_CONFIG_PATH):
        config = {
            "credentials": {"usernames": {}},
            "cookie": {
                "expiry_days": 30,
                "key": "finance_auth_key",
                "name": "finance_auth_cookie"
            }
        }
        with open(AUTH_CONFIG_PATH, "w") as f:
            yaml.dump(config, f)
        return config
    
    with open(AUTH_CONFIG_PATH) as f:
        return yaml.load(f, Loader=SafeLoader)

def save_auth_config(config):
    with open(AUTH_CONFIG_PATH, "w") as f:
        yaml.dump(config, f)

def get_authenticator():
    config = load_auth_config()
    return stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"]
    ), config

def get_current_user():
    if "username" not in st.session_state:
        return None
    return st.session_state["username"]

def require_auth():
    user = get_current_user()
    if not user:
        st.warning("Please login to access this page.")
        st.stop()
    return user

def add_user(username, name, password):
    config = load_auth_config()
    hashed_password = stauth.Hasher.hash(password)
    config["credentials"]["usernames"][username] = {
        "name": name,
        "password": hashed_password
    }
    save_auth_config(config)

def create_user_with_key(username, name, password, key):
    if key != RESET_KEY:
        return False, "Invalid key"
    config = load_auth_config()
    if username in config["credentials"]["usernames"]:
        return False, "Username already exists"
    add_user(username, name, password)
    return True, "User created successfully"

def reset_user_password(username, new_password, reset_key):
    if reset_key != RESET_KEY:
        return False
    config = load_auth_config()
    if username not in config["credentials"]["usernames"]:
        return False
    hashed_password = stauth.Hasher.hash(new_password)
    config["credentials"]["usernames"][username]["password"] = hashed_password
    save_auth_config(config)
    return True
