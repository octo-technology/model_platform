from datetime import datetime

import pandas as pd
import requests
import streamlit

from frontend.api_interactions.endpoints import MODEL_VERSION_ENDPOINT, SEARCH_HUGGING_FACE
from frontend.utils import send_get_query


def get_models_list(url, project_name: str) -> pd.DataFrame | None:
    try:
        response = send_get_query(url.format(project_name=project_name))
        if response["http_code"] == 200:
            return format_models_response(response["data"])
        else:
            streamlit.info(response["data"]["detail"])
            return None
    except requests.RequestException:
        return None


def search_hugging_face_models(search_text: str) -> pd.DataFrame | None:
    try:
        response = send_get_query(SEARCH_HUGGING_FACE.format(SEARCH_ARGS=search_text))
        if response["http_code"] == 200:
            return format_models_response(response["data"])
        elif response["http_code"] == 504:
            raise TimeoutError("504 Hugging face models")
        else:
            return None
    except requests.RequestException:
        return None


def get_model_versions_list(project_name: str, model_name: str) -> pd.DataFrame | None:
    url = MODEL_VERSION_ENDPOINT.format(project_name=project_name, model_name=model_name)
    response = send_get_query(url)
    if response["http_code"] == 200:
        return format_version_list_response(response["data"])
    elif response["http_code"] == 504:
        return "504 Hugging face models"
    else:
        return None


def format_version_list_response(response: list[dict]):
    return [version["version"] for version in response]


def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")


def format_models_response(models):
    data = []
    for model in models:
        model_name = model.get("name", "Unknown")
        creation_timestamp = format_timestamp(model.get("creation_timestamp", 0))
        aliases = ", ".join(model.get("aliases", {}).keys()) if model.get("aliases") else "None"
        versions = model["version"] if "version" in model else model["latest_versions"][0]["version"]

        data.append(
            {
                "Name": model_name,
                "Creation Date": creation_timestamp,
                "Aliases": aliases,
                "Version": versions,
            }
        )

    return pd.DataFrame(data)


def deploy_model(project_name: str, model_name: str, version: str, action_uri: str) -> dict:
    url = action_uri.format(project_name=project_name, model_name=model_name, model_version=version)
    data = send_get_query(url)
    return data["data"]
