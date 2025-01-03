from datetime import datetime

import pandas as pd
import requests


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
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')


def format_response(models):
    data = []
    for model in models:
        model_name = model.get("name", "Unknown")
        deployment_time_stamp = format_timestamp(model.get("deployment_time_stamp", 0))
        versions = len(model.get("latest_versions", []))

        data.append({
            "Name": model_name,
            "Deployment Date": deployment_time_stamp,
            "Versions": versions,
        })

    return pd.DataFrame(data)
