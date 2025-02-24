import uuid

from model_platform import CURRENT_USER
from model_platform.domain.entities.event import Event
from model_platform.domain.entities.project import Project
from model_platform.domain.ports.project_db_handler import ProjectDbHandler
from model_platform.domain.use_cases.deploy_registry import deploy_registry
from model_platform.domain.use_cases.deployed_models import _remove_project_namespace
from model_platform.infrastructure.log_events_handler_json_adapter import LogEventsHandlerJsonAdapter
from model_platform.infrastructure.log_model_deploy_sqlite_adapter import SQLiteLogModelDeployment

log_events = LogEventsHandlerJsonAdapter()


def list_projects(project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects()
    l_projects = [project.to_json() for project in projects]
    log_events.add_event(Event(action=list_projects.__name__, user=uuid.UUID(CURRENT_USER), entity=l_projects))
    return l_projects


def add_project(project_db_handler: ProjectDbHandler, project: Project) -> None:
    log_events.add_event(Event(action=add_project.__name__, user=uuid.UUID(CURRENT_USER), entity=project.name))
    deploy_registry(project.name)
    project_db_handler.add_project(project)


def get_project_info(project_db_handler: ProjectDbHandler, project_name: str) -> dict:
    project = project_db_handler.get_project(project_name)
    log_events.add_event(Event(action=get_project_info.__name__, user=uuid.UUID(CURRENT_USER), entity=project_name))
    return project.to_json()


def remove_project(
    project_db_handler: ProjectDbHandler, deployed_models_sqlite_handler: SQLiteLogModelDeployment, project_name: str
) -> None:
    _remove_project_namespace(project_name)
    project_db_handler.remove_project(project_name)
    deployed_models_sqlite_handler.remove_project_deployments(project_name)
