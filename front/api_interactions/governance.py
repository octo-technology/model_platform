import json

from black.trans import defaultdict

from front.api_interactions.endpoints import PROJECT_GOVERNANCE
from front.utils import send_get_query


def get_project_full_governance(project_name: str):
    result = send_get_query(PROJECT_GOVERNANCE.format(project_name=project_name))
    return result


def get_governance_per_model(project_name: str):
    result = get_project_full_governance(project_name)
    model_governance_dict = defaultdict()
    for row in result["data"]:
        data = row["entity"].replace("'", '"')
        entity = json.loads(data)
        model_name = entity["model_name"]
        model_version = entity["version"]
        deployment_date = entity["deployment_date"]
        action_timestamp = row["timestamp"]
        action = row["action"]
        user = row["user"]
        new_row = {
            "user": user,
            "action": action,
            "action_timestamp": action_timestamp,
            "deployment_date": deployment_date,
            "model_version": model_version,
        }
        if model_name not in model_governance_dict:
            model_governance_dict[model_name] = [new_row]
        else:
            model_governance_dict[model_name].append(new_row)

    return model_governance_dict
