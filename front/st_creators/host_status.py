import streamlit as st

from front.api_interactions.endpoints import HEALTH_ENDPOINT
from front.api_interactions.health import check_url_health


def create_backend_status():
    status, status_icon = check_url_health(HEALTH_ENDPOINT)
    if status == "healthy":
        st.success("Healthy: " + status_icon)
    else:
        st.error("Unhealthy: " + status_icon)
