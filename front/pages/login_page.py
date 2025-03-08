import time

import requests
import streamlit as st
from streamlit_cookies_controller import CookieController

controller = CookieController()

API_URL = "http://0.0.0.0:8001/auth/token"

st.title("Connexion")
token = controller.get("access_token")
st.session_state["token"] = token

if token is None:
    with st.form("login_form"):
        username = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            response = requests.post(API_URL, data={"username": username, "password": password})
            if response.status_code == 200:
                token_data = response.json()
                st.session_state["token"] = token_data["access_token"]
                controller.set("access_token", token_data["access_token"], max_age=3600, secure=False, same_site="Lax")
                st.success("Connexion réussie 🎉")
                if st.session_state["token"] is not None:
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Échec de l'authentication ❌")


if token is not None:
    if st.button("Se déconnecter"):
        st.session_state["token"] = None
        controller.remove("access_token")
        controller.refresh()
