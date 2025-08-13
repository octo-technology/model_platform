import logging
import os

import pandas as pd
import requests
import streamlit as st
from loguru import logger

from frontend.api_interactions.endpoints import ADD_PROJECT_URI, DELETE_PROJECT, PROJECT_INFO_URL, PROJECT_LIST_ENDPOINT
from frontend.api_interactions.health import check_url_health
from frontend.utils import sanitize_name, send_get_query, send_post_query


def get_projects_list() -> pd.DataFrame | None:
    try:
        response = send_get_query(PROJECT_LIST_ENDPOINT, timeout=100)
        if response["http_code"] == 200:
            data = response["data"]
            logger.info(f"Projects list retrieved successfully from backend {data}")
            return format_projects_response(data)
        else:
            st.info(response["data"]["detail"])
            return None
    except requests.RequestException:
        return None


def format_projects_response(projects: dict) -> pd.DataFrame:
    data = []
    for project in projects:
        registry_homepage = build_project_registry_url(project.get("name", "Unknown"))
        registry_status = build_healthcheck_status_url(registry_homepage)
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


def build_healthcheck_status_url(registry_homepage: str) -> str:
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
        st.toast("Project added successfully", icon="✅")
    else:
        st.error(f"Failed to add project:{response['data']['detail']}", icon="❌")


def format_users_list(users_df: list[dict]) -> pd.DataFrame:
    data = []
    for user in users_df:
        data.append(
            {
                "Name": user.get("email", "Unknown"),
                "Role": user.get("role", "Unknown"),
            }
        )
    return pd.DataFrame(data)


def delete_project(project_name: str):
    url = DELETE_PROJECT.format(project_name=project_name)
    result = send_get_query(url)
    if result["http_code"] != 200:
        st.session_state["display_delete_project_success"] = False
    else:
        st.session_state["display_delete_project_success"] = project_name
    return result
