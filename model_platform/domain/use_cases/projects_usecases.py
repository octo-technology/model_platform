import uuid

from model_platform import CURRENT_USER
from model_platform.domain.entities.event import Event
from model_platform.domain.entities.project import Project
from model_platform.domain.ports.project_db_handler import ProjectDbHandler
from model_platform.domain.use_cases.deploy_registry import deploy_registry
from model_platform.domain.use_cases.deployed_models import _remove_project_namespace
from model_platform.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()


def list_projects(project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects()
    l_projects = [project.to_json() for project in projects]
    return l_projects


def add_project(project_db_handler: ProjectDbHandler, project: Project) -> bool:
    EVENT_LOGGER.add_event(
        Event(action=add_project.__name__, user=uuid.UUID(CURRENT_USER), entity=project), project_name=project.name
    )
    deploy_registry(project.name)
    status = project_db_handler.add_project(project)
    return status


def get_project_info(project_db_handler: ProjectDbHandler, project_name: str) -> Project:
    project = project_db_handler.get_project(project_name)
    return project


def remove_project(project_db_handler: ProjectDbHandler, project_name: str) -> bool:
    _remove_project_namespace(project_name)
    project_db_handler.remove_project(project_name)
    EVENT_LOGGER.add_event(
        Event(action=remove_project.__name__, user=uuid.UUID(CURRENT_USER), entity=project_name), project_name
    )
    return True

