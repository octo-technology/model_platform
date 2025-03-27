import re

import requests
import streamlit as st
from streamlit_cookies_controller import CookieController


def sanitize_name(project_name: str) -> str:
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", project_name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    return sanitized_name


def send_get_query(url: str, timeout: int = 10) -> dict:
    """Envoie une requête GET à l'URL et retourne le contenu JSON."""
    token = st.session_state["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, timeout=timeout)
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}

    return {"http_code": response.status_code, "data": data}


def send_post_query(url: str, json_data: dict):
    token = st.session_state["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=json_data)
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        data = {}
    return {"http_code": response.status_code, "data": data}


def set_token_in_session_state():
    controller = CookieController()
    token = controller.get("access_token")
    st.session_state["token"] = token
    return controller
