import streamlit as st
from loguru import logger
from streamlit_autorefresh import st_autorefresh

from frontend.api_interactions.endpoints import ARTIFACTS_ENDPOINT, HEALTH_ENDPOINT
from frontend.st_creators.governance_page.governance_main_page import create_governance_main_page
from frontend.st_creators.host_status import create_backend_status
from frontend.st_creators.login_container import create_login_container, create_logout_container
from frontend.st_creators.project_page.project_page_items import (
    create_add_model_deployment_success,
    create_add_model_undeploy_success,
    create_add_user_success,
    create_changed_user_role_success,
)
from frontend.st_creators.projects_page import create_projects_page
from frontend.utils import set_token_in_session_state

logger.info("On main page")
st.set_page_config(layout="wide", page_title="Model platform")

st_autorefresh(interval=20 * 1000, key="refresh")

with open("frontend/assets/style.css") as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

cookie_controller = set_token_in_session_state()


def set_current_page_to_display(page_to_display):
    st.session_state["current_page_to_display"] = page_to_display
    st.session_state["project_users_to_display"] = None


with st.container(border=True):
    if st.session_state["token"] is None:
        create_login_container(cookie_controller)
    else:
        logger.info("Token ok")
        with st.sidebar:
            st.image("frontend/assets/octo_logo_png.png", use_container_width=True)
            st.markdown("# Model Platform")
            with st.container(border=True):
                st.markdown("### GENERAL")
                st.button(
                    ":blue[Projects]",
                    key="sidebar_projects_button",
                    on_click=set_current_page_to_display,
                    args=["Projects"],
                    type="tertiary",
                )
                st.button(
                    ":blue[Governance]",
                    key="sidebar_governance_button",
                    on_click=set_current_page_to_display,
                    args=["Governance"],
                    type="tertiary",
                )
            with st.container(border=True):
                st.markdown("### OTHER")
                create_logout_container(cookie_controller)
            with st.container(border=True):
                st.markdown("### Model Platform backend status :")
                create_backend_status(HEALTH_ENDPOINT)
                st.markdown("### Artifact Storage Status :")
                create_backend_status(ARTIFACTS_ENDPOINT)

if st.session_state.get("current_page_to_display", None) == "Projects":
    create_projects_page()
elif st.session_state.get("current_page_to_display", None) == "Governance":
    create_governance_main_page()

if st.session_state.get("added_user_to_project_success", None):
    create_add_user_success()

if st.session_state.get("action_model_deployment_ok", None):
    create_add_model_deployment_success()

if st.session_state.get("action_model_undeploy_ok", None):
    create_add_model_undeploy_success()

if st.session_state.get("change_user_role_for_project_success", None):
    create_changed_user_role_success()
