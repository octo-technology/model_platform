from datetime import datetime

import pandas as pd
import requests
import streamlit

from front.api_interactions.endpoints import BUILD_DEPLOY_STATUS_ENDPOINT, DEPLOYED_MODEL_URI
from front.api_interactions.health import check_url_health
from front.utils import send_get_query


def get_deployed_models_list(url) -> pd.DataFrame | None:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return format_response(response.json())
        else:
            return None
    except requests.RequestException:
        return None


def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")


def format_response(models):
    data = []
    for model, status in models:
        model_name = model["model_name"]
        deployment_time_stamp = model["deployment_date"]
        versions = model["version"]
        status = status
        uri = DEPLOYED_MODEL_URI.format(
            project_name=streamlit.session_state["selected_project"], deployment_name=model["deployment_name"]
        )
        health = check_url_health(uri + "/health")

        data.append(
            {
                "Name": model_name,
                "Deployment Date": deployment_time_stamp,
                "version": versions,
                "Deployment exists": status,
                "Health check": health,
                "uri": uri,
            }
        )

    return pd.DataFrame(data)


def get_build_status(project_name, task_id):
    url = BUILD_DEPLOY_STATUS_ENDPOINT.format(project_name=project_name, task_id=task_id)
    data = send_get_query(url)
    return data["data"]["status"]
