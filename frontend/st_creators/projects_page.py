import streamlit as st

from frontend.api_interactions.projects import get_projects_list
from frontend.st_creators.project_page.project_listing import create_projects_listing
from frontend.st_creators.project_page.project_page_items import (
    create_add_user_success,
    create_changed_user_role_success,
    create_delete_project_success,
    create_project_settings,
)


def create_projects_page():
    projects_list_df = get_projects_list()
    find_project_button_clicked()
    clicked_project_name = st.session_state.get("project_users_to_display", None)
    if clicked_project_name is not None:
        st.markdown(f"# {clicked_project_name}")
        create_project_settings(projects_list_df, clicked_project_name)
    else:
        st.markdown("# Projects")
        create_projects_listing(projects_list_df)
    if st.session_state.get("display_delete_project_success", False):
        create_delete_project_success()
    if st.session_state.get("added_user_to_project_success", False):
        create_add_user_success()
    if st.session_state.get("changed_user_role_project_success", False):
        create_changed_user_role_success()


def find_project_button_clicked() -> str | None:
    clicked_button = None
    for key in st.session_state.keys():
        if "clicked_project_Name_" in key and st.session_state[key]:
            clicked_button = key.replace("clicked_project_Name_", "")
            st.session_state["project_users_to_display"] = clicked_button
    return clicked_button
