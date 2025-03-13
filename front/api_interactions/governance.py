from front.api_interactions.endpoints import PROJECT_GOVERNANCE
from front.utils import send_get_query


def get_project_full_governance(project_name: str):
    result = send_get_query(PROJECT_GOVERNANCE.format(project_name=project_name))
    return result


def download_project_governance(project_name: str):
    send_get_query(PROJECT_GOVERNANCE.format(project_name=project_name))
