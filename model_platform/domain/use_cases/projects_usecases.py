import uuid

from model_platform import CURRENT_USER

from model_platform.domain.entities.project import Project
from model_platform.domain.entities.event import Event
from model_platform.domain.entities.project import Project
from model_platform.domain.ports.project_db_handler import ProjectDbHandler

from model_platform.infrastructure.log_events_handler_json_adapter import LogEventsHandlerJsonAdapter

log_events = LogEventsHandlerJsonAdapter()


def list_projects(project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects()
    l_projects = [project.to_json() for project in projects]
    log_events.add_event(
        Event(
            action=list_projects.__name__,
            user=uuid.UUID(CURRENT_USER),
            entity=l_projects
        )
    )
    return l_projects


def add_project(project_db_handler: ProjectDbHandler, project: Project) -> None:
    project_db_handler.add_project(project)
    log_events.add_event(Event(action=add_project.__name__, user=uuid.UUID(CURRENT_USER), entity=project.name))
    log_events.add_event(
        Event(
            action=add_project.__name__,
            user=uuid.UUID(CURRENT_USER),
            entity=project.name
        )
    )
    deploy_registry(project.name)


def remove_project_namespace(project_name: str) -> None:
    k8s_deployment = K8SRegistryDeployment(project_name)
    k8s_deployment.delete_namespace()


def remove_project(project_db_handler: ProjectDbHandler, project_name: str) -> None:
    project_db_handler.remove_project(project_name)
    remove_project_namespace(project_name)


def get_project_info(project_db_handler: ProjectDbHandler, project_name: str) -> dict:
    project = project_db_handler.get_project(project_name)
    log_events.add_event(
        Event(
            action=get_project_info.__name__,
            user=uuid.UUID(CURRENT_USER),
            entity=project_name
        )
    )
    return project.to_json()

