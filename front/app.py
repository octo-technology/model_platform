import streamlit as st
from loguru import logger

from front.st_creators.host_status import create_backend_status
from front.st_creators.login_container import create_login_container, create_logout_container
from front.st_creators.projects_page import create_projects_page
from front.utils import set_token_in_session_state

logger.info("Application Streamlit démarrée")
st.set_page_config(layout="wide")

with open("front/assets/style.css") as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

cookie_controller = set_token_in_session_state()


def set_current_page_to_display(page_to_display):
    st.session_state["current_page_to_display"] = page_to_display
    st.session_state["project_users_to_display"] = None


with st.container(border=True):
    if st.session_state["token"] is None:
        create_login_container(cookie_controller)
    else:
        with st.sidebar:
            st.image("front/assets/octo_logo_png.png", use_container_width=True)
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
                st.button(":blue[Governance]", key="sidebar_governance_button", type="tertiary")
            with st.container(border=True):
                st.markdown("### OTHER")
                create_logout_container(cookie_controller)
            with st.container(border=True):
                st.markdown("### Model Platform backend status :")
                create_backend_status()

if st.session_state.get("current_page_to_display", None) == "Projects":
    create_projects_page()
