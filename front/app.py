import os

import streamlit as st
from loguru import logger

from front.api_interactions.endpoints import HEALTH_ENDPOINT
from front.api_interactions.health import check_url_health
from front.dot_env import DotEnv
from front.utils import sanitize_name

DotEnv()
logger.info("Application Streamlit démarrée")

pg = st.navigation(
    [
        st.Page("pages/project_page.py", title="🤖 Project page"),
        st.Page("pages/project_manage_page.py", title="⚙️ Manage project"),
        st.Page("pages/create_project_page.py", title="➕️ Create project"),
    ]
)

pg.run()

# Affichage de l'état avec une pastille
st.sidebar.title("Backend status")
status_colors = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}
status = check_url_health(HEALTH_ENDPOINT)
st.sidebar.markdown(f"{status_colors[status]} {status.capitalize()}")


if st.session_state["selected_project"]:
    st.sidebar.title("Registry status")
    status_colors = {"healthy": "🟢", "unhealthy": "🟠", "unreachable": "🔴"}
    project_name = st.session_state["selected_project"]
    status = check_url_health(
        "http://"
        + os.environ["MP_HOST_NAME"]
        + "/"
        + os.environ["MP_REGISTRY_PATH"]
        + "/"
        + sanitize_name(project_name)
    )
    st.sidebar.markdown(f"{status_colors[status]} {status.capitalize()}")
