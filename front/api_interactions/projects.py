import logging
import os

import pandas as pd
import requests
import streamlit as st

from front.api_interactions.endpoints import ADD_PROJECT_URI, PROJECT_INFO_URL, PROJECT_LIST_ENDPOINT
from front.api_interactions.health import check_url_health
from front.utils import sanitize_name, send_get_query, send_post_query


def get_projects_list() -> pd.DataFrame | None:
    try:
        response = send_get_query(PROJECT_LIST_ENDPOINT)
        if response["http_code"] == 200:
            return format_projects_response(response["data"])
        else:
            st.info(response["data"]["detail"])
            return None
    except requests.RequestException:
        return None


def format_projects_response(projects: dict) -> pd.DataFrame:
    data = []
    for project in projects:
        registry_homepage = build_project_registry_url(project.get("name", "Unknown"))
        registry_status = build_project_registry_status_url(registry_homepage)
        data.append(
            {
                "Name": project.get("name", "Unknown"),
                "Owner": project.get("owner", "Unknown"),
                "Scope": project.get("scope", "Unknown"),
                "Data perimeter": project.get("data_perimeter", "Unknown"),
                "Registry homepage": f"[Registry Homepage]({registry_homepage})",
                "Registry status": registry_status,
            }
        )
    return pd.DataFrame(data)


def build_project_registry_url(project_name: str) -> str:
    project_registry_url = (
        "http://"
        + os.environ["MP_HOST_NAME"]
        + "/"
        + os.environ["MP_REGISTRY_PATH"]
        + "/"
        + sanitize_name(project_name)
        + "/"
    )
    return project_registry_url


def build_project_registry_status_url(registry_homepage: str) -> str:
    status, status_icon = check_url_health(registry_homepage)
    if status == "healthy":
        return ":green[Healthy] " + status_icon
    else:
        return ":red[Unhealthy] " + status_icon


def get_project_info(project_name) -> pd.DataFrame | None:
    try:
        response = send_get_query(PROJECT_INFO_URL.format(PROJECT_NAME=project_name))
        if response["http_code"] == 200:
            return pd.DataFrame(response["data"], index=["Info"]).T
        else:
            return None
    except requests.RequestException:
        return None


def add_project(name, owner, scope, data_perimeter) -> bool:
    logging.debug(f"Posting to {ADD_PROJECT_URI}")
    json = {
        "name": name,
        "owner": owner,
        "scope": scope,
        "data_perimeter": data_perimeter,
    }
    response = send_post_query(ADD_PROJECT_URI, json)
    if response["http_code"] == 200:
        st.success("Project added successfully")
    else:
        st.error(f"Failed to add project:{response['data']['detail']}")


def create_projects_listing(show_delete_button: bool = True):
    projects_list_df = get_projects_list()
    if projects_list_df is not None and not projects_list_df.empty:
        if show_delete_button:
            columns = list(projects_list_df.columns) + ["Delete project"]
        else:
            columns = list(projects_list_df.columns)
        col_sizes = [2] * (len(columns))
        col_objects = st.columns(col_sizes)
        for col_obj, col_name in zip(col_objects, columns):
            col_obj.write(f"**{col_name}**")
        for _, row in projects_list_df.iterrows():
            col_objects = st.columns(col_sizes)
            for col_obj, col_name in zip(col_objects, columns):
                if col_name in projects_list_df.columns:
                    col_obj.write(row[col_name])
            if show_delete_button:
                with col_objects[-1]:
                    build_project_deletion_bin(row["Name"])


def set_bool_display_delete_dialog(value: bool) -> bool:
    st.session_state["display_delete_dialog"] = value


def build_project_deletion_bin(project_name: str):
    st.session_state["show_delete_dialog"] = None
    st.button(
        label="",
        icon="🗑️",
        type="tertiary",
        key=f"delete_project_{project_name}",
        use_container_width=True,
        on_click=set_bool_display_delete_dialog,
        args=[True],
    )

    if st.session_state.get("display_delete_dialog", False):
        create_st_dialog_delete_project(project_name)


@st.dialog("Project Deletion Confirmation")
def create_st_dialog_delete_project(project_name: str):
    st.write(f"Are you sure you want to delete the project **{project_name}**?")
    st.session_state["current_page_to_display"] = "Projects"
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, delete", key=f"confirm_delete_{project_name}"):
            delete_project(project_name)
            st.session_state["display_delete_dialog"] = False
            st.rerun()

    with col2:
        if st.button("Cancel", key=f"cancel_delete_{project_name}"):
            st.session_state["display_delete_dialog"] = False
            st.rerun()


def delete_project(project_name: str):
    st.session_state["display_delete_project_success"] = project_name


def display_delete_project_success(project_name: str):
    st.toast(f"Delete project {project_name} successfully", icon="✅")
    st.session_state["display_delete_project_success"] = False
