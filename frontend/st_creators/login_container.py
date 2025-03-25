import time

import requests
import streamlit as st

from frontend.api_interactions.endpoints import AUTH_URI
from frontend.api_interactions.users import create_user


def create_login_container(cookie_controller):
    st.title("Welcome to Model Platform")

    st.info("Please enter your details")
    token = cookie_controller.get("access_token")
    st.session_state["token"] = token

    if token is None and not st.session_state.get("create_account", False):
        with st.form("login_form"):
            username = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                response = requests.post(AUTH_URI, data={"username": username, "password": password})
                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state["token"] = token_data["access_token"]
                    cookie_controller.set(
                        "access_token", token_data["access_token"], max_age=3600, secure=False, same_site="Lax"
                    )
                    st.success("Logged in successfully 🎉")
                    if st.session_state["token"] is not None:
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Login failed ❌")
        create_account_creator_link()
    else:
        create_account_creation_form()


def create_account_creator_link():
    if st.button(":blue[Don't have an account? Create one here]", type="tertiary"):
        st.session_state["create_account"] = True
        st.rerun()


def go_back_to_login_link():
    if st.button(":blue[Go back to login page]", type="tertiary"):
        st.session_state["create_account"] = False
        st.rerun()


def create_account_creation_form():
    with st.form("create_account_form"):
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password_password_confirmation = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create account")
        if submitted and password != "" and password_password_confirmation == password:
            response = create_user(username, password)
            if response:
                st.success("Account created successfully 🎉")
            else:
                st.error("Account creation failed ❌")
    go_back_to_login_link()


def create_logout_container(cookie_controller):
    token = cookie_controller.get("access_token")
    if token is not None:
        if st.button(":blue[Logout]", type="tertiary"):
            st.session_state["token"] = None
            cookie_controller.remove("access_token")
            cookie_controller.refresh()
            st.session_state["current_page_to_display"] = None
