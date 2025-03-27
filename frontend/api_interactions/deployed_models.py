from datetime import datetime

import pandas as pd
import streamlit as st

from backend.utils import sanitize_project_name
from frontend.api_interactions.endpoints import (
    BUILD_DEPLOY_STATUS_ENDPOINT,
    DEPLOYED_MODEL_URI,
    DEPLOYED_MODELS_LIST_ENDPOINT,
    GET_HF_MODEL_ENDPOINT,
    UNDEPLOY_MODEL_ENDPOINT,
)
from frontend.api_interactions.projects import build_healthcheck_status_url
from frontend.utils import send_get_query


def get_deployed_models_list(project_name: str) -> pd.DataFrame | None:
    url = DEPLOYED_MODELS_LIST_ENDPOINT.format(project_name=project_name)
    response = send_get_query(url)
    if response["http_code"] == 200:
        return format_response(response["data"], project_name)
    else:
        st.info(response["data"]["detail"])
        return None


def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")


def format_response(models: list, project_name: str):
    data = []
    for model in models:
        model_name = model["model_name"]
        deployment_time_stamp = model["deployment_date"]
        versions = model["version"]
        uri = DEPLOYED_MODEL_URI.format(
            project_name=sanitize_project_name(project_name), deployment_name=model["deployment_name"]
        )
        health = build_healthcheck_status_url(uri + "/health")
        data.append(
            {
                "Name": model_name,
                "Deployment Date": deployment_time_stamp,
                "version": versions,
                "Health check": health,
                "Url": uri + "/health",
            }
        )

    return pd.DataFrame(data)


def get_build_status(project_name, task_id):
    url = BUILD_DEPLOY_STATUS_ENDPOINT.format(project_name=project_name, task_id=task_id)
    data = send_get_query(url)
    return data["data"]["status"]


def undeploy_model(project_name, model_name: str, version: str):
    url = UNDEPLOY_MODEL_ENDPOINT.format(project_name=project_name, model_name=model_name, model_version=version)
    response = send_get_query(url)
    if response["http_code"] == 200:
        return True
    else:
        return False


def get_model(project_name, model_name: str):
    url = GET_HF_MODEL_ENDPOINT.format(project_name=project_name, model_id=model_name)
    response = send_get_query(url)
    if response["http_code"] == 200:
        return True
    else:
        return False
