from enum import Enum


class Role(Enum):
    ADMIN = "ADMIN"
    SIMPLE_USER = "SIMPLE_USER"


class ProjectRole(Enum):
    NO_ROLE = "NO_ROLE"
    VIEWER = "VIEWER"
    DEVELOPER = "DEVELOPER"
    MAINTAINER = "MAINTAINER"
    ADMIN = "ADMIN"


PROJECT_ACTIONS_MINIMUM_LEVEL = {ProjectRole.NO_ROLE: []}
PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.VIEWER] = PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.NO_ROLE] + [
    "route_project_info",
    "list_models",
    "list_deployed_models",
    "list_model_versions",
    "route_list_projects",
]
PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.DEVELOPER] = PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.VIEWER] + [
    "route_deploy_model",
    "route_undeploy",
    "check_task_status",
]
PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.MAINTAINER] = PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.DEVELOPER] + [
    "route_project_governance",
    "route_add_user_to_project",
    "get_users_for_project",
    "route_remove_user_from_project",
    "route_change_user_role_for_project",
]
PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.ADMIN] = PROJECT_ACTIONS_MINIMUM_LEVEL[ProjectRole.MAINTAINER] + [
    "governance_route",
    "download_governance_route",
]
