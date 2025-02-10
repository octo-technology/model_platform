from datetime import datetime

import pandas as pd
import requests

from front.api_interactions.endpoints import DEPLOY_MODEL_ENDPOINT


def get_models_list(url, project_name: str) -> pd.DataFrame | None:
    try:
        response = requests.get(url.format(project_name=project_name), timeout=5)
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
        versions = len(model.get("latest_versions", []))

        data.append(
            {
                "Name": model_name,
                "Creation Date": creation_timestamp,
                "Aliases": aliases,
                "Versions": versions,
            }
        )

    return pd.DataFrame(data)


def deploy_model(model_name):
    try:
        response = requests.post(f"{DEPLOY_MODEL_ENDPOINT}/{model_name}", timeout=5)
        if response.status_code == 200:
            return f"Model {model_name} deployed successfully."
        else:
            return f"Failed to deploy model {model_name}."
    except requests.RequestException:
        return "Error contacting the deployment API."
