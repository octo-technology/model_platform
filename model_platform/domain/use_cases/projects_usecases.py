from model_platform.domain.entities.project import Project
from model_platform.domain.ports.project_db_handler import ProjectDbHandler


def list_projects(project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects()
    return [project.to_json() for project in projects]


def add_project(project_db_handler: ProjectDbHandler, project: Project) -> None:
    project_db_handler.add_project(project)


def get_project_info(project_db_handler: ProjectDbHandler, project_name: str) -> dict:
    project = project_db_handler.get_project(project_name)
    return project.to_json()
