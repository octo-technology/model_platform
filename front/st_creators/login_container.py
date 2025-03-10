import time

import requests
import streamlit as st

from front.api_interactions.endpoints import AUTH_URI


def create_login_container(cookie_controller):
    st.title("Welcome to Model Platform")

    st.info("Please enter your details")
    token = cookie_controller.get("access_token")
    st.session_state["token"] = token

    if token is None:
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


def create_logout_container(cookie_controller):
    token = cookie_controller.get("access_token")
    if token is not None:
        if st.button("Logout"):
            st.session_state["token"] = None
            cookie_controller.remove("access_token")
            cookie_controller.refresh()
