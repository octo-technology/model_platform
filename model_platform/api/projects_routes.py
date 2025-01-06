from fastapi import APIRouter

from model_platform.domain.entities.project import Project
from model_platform.domain.use_cases.projects_usecases import add_project, get_project_info, list_projects
from model_platform.infrastructure.project_sqlite_db_handler import ProjectSQLiteDBHandler

router = APIRouter()

# Fix data to test front
PROJECT_NAMES = ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta"]
PROJECTS_INFOS = {
    project_name: {
        "name": project_name,
        "owner": project_name.split(" ")[-1] + " team",
        "scope": "A project to revolutionize IA projects",
        "data_perimeter": "All data on earth regarding our clients",
    }
    for project_name in PROJECT_NAMES
}

PROJECT_SQLITE_DB_HANDLER = ProjectSQLiteDBHandler("projects.db")


@router.get("/list")
def route_list_projects():
    return list_projects(project_db_handler=PROJECT_SQLITE_DB_HANDLER)


@router.get("/{project_name}/info")
def route_project_info(project_name: str):
    return get_project_info(PROJECT_SQLITE_DB_HANDLER, project_name=project_name)


@router.post("/add")
def route_add_project(project: Project):
    return add_project(project_db_handler=PROJECT_SQLITE_DB_HANDLER, project=project)
