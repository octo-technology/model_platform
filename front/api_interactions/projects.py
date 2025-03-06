import logging

import pandas as pd
import requests
import streamlit as st

from front.api_interactions.endpoints import ADD_PROJECT_URI, PROJECT_INFO_URL, PROJECT_LIST_ENDPOINT
from front.utils import send_get_query, send_post_query


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
        data.append(
            {
                "Name": project.get("name", "Unknown"),
                "Owner": project.get("owner", "Unknown"),
                "Scope": project.get("scope", "Unknown"),
                "Data perimeter": project.get("data_perimeter", "Unknown"),
            }
        )
    return pd.DataFrame(data)


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
