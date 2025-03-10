import streamlit as st
from loguru import logger

from front.st_creators.host_status import create_backend_status
from front.st_creators.login_container import create_login_container, create_logout_container
from front.st_creators.projects_page import create_projects_page
from front.utils import set_token_in_session_state

logger.info("Application Streamlit démarrée")
st.set_page_config(layout="wide")
cookie_controller = set_token_in_session_state()


def set_current_page_to_display(page_to_display):
    st.session_state["current_page_to_display"] = page_to_display


with st.container(border=True):
    if st.session_state["token"] is None:
        create_login_container(cookie_controller)
    else:
        with st.sidebar:
            st.markdown("# Model Platform")
            with st.container(border=True):
                st.markdown("### GENERAL")
                st.button(
                    "Projects", key="sidebar_projects_button", on_click=set_current_page_to_display, args=["Projects"]
                )
                st.button("Governance", key="sidebar_governance_button")
            with st.container(border=True):
                st.markdown("### OTHER")
                create_logout_container(cookie_controller)
            with st.container(border=True):
                st.markdown("### Model Platform backend status :")
                create_backend_status()

if st.session_state.get("current_page_to_display", None) == "Projects":
    create_projects_page()
