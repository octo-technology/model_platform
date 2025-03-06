import re

import requests
import streamlit as st


def sanitize_name(project_name: str) -> str:
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", project_name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    return sanitized_name


def send_get_query(url: str) -> dict:
    """Envoie une requête GET à l'URL et retourne le contenu JSON."""
    token = st.session_state["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(url)
    response = requests.get(url, headers=headers)
    print(response)
    return {"http_code": response.status_code, "data": response.json()}


def send_post_query(url: str, json_data: dict):
    token = st.session_state["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=json_data)
    return {"http_code": response.status_code, "data": response.json()}
