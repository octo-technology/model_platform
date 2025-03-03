import json
from json import JSONDecodeError

from front.api_interactions.endpoints import PROJECT_GOVERNANCE
from front.utils import send_get_query


def get_project_full_governance(project_name: str):
    result = send_get_query(PROJECT_GOVERNANCE.format(project_name=project_name))
    return result


def get_governance_per_model(project_name: str):
    result = get_project_full_governance(project_name)
    model_governance = []
    if result["data"] is None:
        return None
    for row in result["data"]:
        data = row["entity"].replace("'", '"')
        try:
            entity = json.loads(data)
        except JSONDecodeError:
            entity = row["entity"]

        action_timestamp = row["timestamp"]
        action = row["action"]
        user = row["user"]
        new_row = {"user": user, "action": action, "action_timestamp": action_timestamp, "entity": entity}

        model_governance.append(new_row)

    return model_governance
