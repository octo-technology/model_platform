import requests
import streamlit as st

from front.api_interactions.health import check_url_health


def create_backend_status(url: str):
    try:
        status, status_icon = check_url_health(url)
        if status == "healthy":
            st.success("Healthy: " + status_icon)
        elif status == "unhealthy":
            st.info("Unhealthy: " + status_icon)
    except requests.exceptions.ConnectionError:
        st.error("Unhealthy: " + "🔴")
