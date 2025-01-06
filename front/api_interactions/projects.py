import logging

import pandas as pd
import requests

from front.api_interactions.endpoints import ADD_PROJECT_URI, PROJECT_INFO_URL, PROJECT_LIST_ENDPOINT


def get_projects_list() -> pd.DataFrame | None:
    try:
        response = requests.get(PROJECT_LIST_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return format_projects_response(response.json())
        else:
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
        response = requests.get(PROJECT_INFO_URL.format(PROJECT_NAME=project_name), timeout=5)
        if response.status_code == 200:
            return pd.DataFrame(response.json(), index=["Info"]).T
        else:
            return None
    except requests.RequestException:
        return None


def add_project(name, owner, scope, data_perimeter) -> bool:
    logging.debug(f"Posting to {ADD_PROJECT_URI}")
    response = requests.post(
        ADD_PROJECT_URI,
        json={
            "name": name,
            "owner": owner,
            "scope": scope,
            "data_perimeter": data_perimeter,
        },
    )
    if response.status_code == 200:
        return True
    else:
        return False
