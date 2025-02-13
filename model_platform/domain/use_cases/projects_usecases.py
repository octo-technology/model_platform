from model_platform.domain.entities.project import Project
from model_platform.domain.ports.project_db_handler import ProjectDbHandler
from model_platform.domain.use_cases.deploy_registry import deploy_registry, remove_registry


def list_projects(project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects()
    return [project.to_json() for project in projects]


def add_project(project_db_handler: ProjectDbHandler, project: Project) -> None:
    project_db_handler.add_project(project)
    deploy_registry(project.name)


def remove_project(project_db_handler: ProjectDbHandler, project_name: str) -> None:
    project_db_handler.remove_project(project_name)
    remove_registry(project_name)


def get_project_info(project_db_handler: ProjectDbHandler, project_name: str) -> dict:
    project = project_db_handler.get_project(project_name)
    return project.to_json()
