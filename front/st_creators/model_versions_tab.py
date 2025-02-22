import streamlit

from front.api_interactions.endpoints import MODEL_VERSION_ENDPOINT
from front.api_interactions.models import get_model_versions_list
from front.st_creators.project_page_items import build_model_version_listing


def model_versions_tab():
    model_name = streamlit.session_state["list_versions"]
    model_versions = get_model_versions_list(
        MODEL_VERSION_ENDPOINT, streamlit.session_state["selected_project"], model_name
    )
    build_model_version_listing(model_versions, elements_to_add=["Deploy"])
    close_tab_button()


def close_tab_button():
    if streamlit.button("Close tab", key="close_tab_button"):
        streamlit.session_state["tabs"] = ["Project's models"]
        streamlit.session_state.pop("list_versions")
        streamlit.rerun()
