from datetime import datetime

import pandas as pd
import requests


def get_models_list(url, project_name: str) -> pd.DataFrame | None:
    try:
        response = requests.get(url.format(project_name=project_name), timeout=5)
        if response.status_code == 200:
            return format_models_response(response.json())
        else:
            return None
    except requests.RequestException:
        return None


def get_model_versions_list(url, project_name: str, model_name: str) -> pd.DataFrame | None:
    try:
        response = requests.get(url.format(project_name=project_name, model_name=model_name), timeout=5)
        if response.status_code == 200:
            return format_models_response(response.json())
        else:
            return None
    except requests.RequestException:
        return None


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
                "version": versions,
            }
        )

    return pd.DataFrame(data)


def deploy_model(project_name: str, model_name: str, version: str, action_uri: str) -> str:
    try:
        response = requests.get(
            action_uri.format(project_name=project_name, model_name=model_name, model_version=version), timeout=5
        )
        if response.status_code == 200:
            return "Action complete successfully."
        else:
            return "Failed to perform action."
    except requests.RequestException:
        return "Error contacting the deployment API."
