# Philippe Stepniewski
from loguru import logger

from backend.domain.entities.project import Project
from backend.domain.ports.object_storage_handler import ObjectStorageHandler
from backend.domain.ports.project_db_handler import ProjectDbHandler
from backend.domain.use_cases.deploy_registry import deploy_registry
from backend.domain.use_cases.deployed_models import _remove_project_namespace
from backend.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()


def list_projects(project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects()
    l_projects = [project.to_json() for project in projects]
    logger.info(f"Projects listed: {l_projects}")
    return l_projects


def list_projects_for_user(user: str, project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects_for_user(user)
    l_projects = [project.to_json() for project in projects]
    return l_projects


def add_project(project_db_handler: ProjectDbHandler, project: Project, object_storage: ObjectStorageHandler) -> bool:
    deploy_registry(project.name)
    if project.batch_enabled:
        object_storage.ensure_project_space(project.name)
    status = project_db_handler.add_project(project)
    return status


def get_project_info(project_db_handler: ProjectDbHandler, project_name: str) -> Project:
    project = project_db_handler.get_project(project_name)
    return project


def remove_project(
    project_db_handler: ProjectDbHandler, project_name: str, object_storage: ObjectStorageHandler
) -> bool:
    try:
        _remove_project_namespace(project_name)
    except Exception as e:
        logger.error(f"K8s cleanup failed for project '{project_name}', continuing with DB removal: {e}")
    try:
        object_storage.remove_project_space(project_name)
    except Exception as e:
        logger.error(f"Storage cleanup failed for project '{project_name}', continuing with DB removal: {e}")
    project_db_handler.remove_project(project_name)
    return True


def update_project_batch_enabled(
    project_db_handler: ProjectDbHandler,
    project_name: str,
    batch_enabled: bool,
    object_storage: ObjectStorageHandler,
) -> bool:
    if batch_enabled:
        object_storage.ensure_project_space(project_name)
    else:
        object_storage.remove_project_space(project_name)
    project_db_handler.update_batch_enabled(project_name, batch_enabled)
    return True
