import os

import streamlit as st
from black.trans import defaultdict
from loguru import logger

from front.api_interactions.endpoints import HEALTH_ENDPOINT
from front.api_interactions.health import check_url_health
from front.utils import sanitize_name, set_token_in_session_state

logger.info("Application Streamlit démarrée")
st.set_page_config(layout="wide")
set_token_in_session_state()

if st.session_state["token"] is None:
    st.info("Please login to access the application.")
    pg = st.navigation([st.Page("pages/login_page.py", title="🔒 Login")])

    pg.run()
else:
    st.session_state["deployment_task_id"] = defaultdict()

    pg = st.navigation(
        [
            st.Page("pages/login_page.py", title="🔒 Login"),
            st.Page("pages/project_page.py", title="🤖 Project page"),
            st.Page("pages/project_manage_page.py", title="⚙️ Manage project"),
            st.Page("pages/create_project_page.py", title="➕️ Create project"),
        ]
    )

    pg.run()

    # Affichage de l'état avec une pastille
    st.sidebar.title("Backend status")

    status, status_icon = check_url_health(HEALTH_ENDPOINT)
    st.sidebar.markdown(f"{status_icon} {status.capitalize()}")

    if "selected_project" in st.session_state and st.session_state["selected_project"]:
        st.sidebar.title("Registry status")
        project_name = st.session_state["selected_project"]
        project_registry_url = (
            "http://"
            + os.environ["MP_HOST_NAME"]
            + "/"
            + os.environ["MP_REGISTRY_PATH"]
            + "/"
            + sanitize_name(project_name)
            + "/"
        )
        status, status_icon = check_url_health(project_registry_url)
        st.sidebar.markdown(f"{status_icon} {status.capitalize()}")
        st.sidebar.link_button("Project registry homepage", project_registry_url)
