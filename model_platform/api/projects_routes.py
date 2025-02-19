from fastapi import APIRouter, Depends, Request

from model_platform.domain.entities.project import Project
from model_platform.domain.use_cases.projects_usecases import (
    add_project,
    get_project_info,
    list_projects,
    remove_project,
)
from model_platform.infrastructure.log_model_deploy_sqlite_adapter import SQLiteLogModelDeployment
from model_platform.infrastructure.project_sqlite_db_handler import ProjectSQLiteDBHandler

router = APIRouter()


def get_project_sqlite_db_handler(request: Request):
    return request.app.state.project_sqlite_db_handler


def get_deployed_models_sqlite_handler(request: Request) -> SQLiteLogModelDeployment:
    return request.app.state.deployed_models_db


@router.get("/list")
def route_list_projects(project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler)):
    return list_projects(project_db_handler=project_sqlite_db_handler)


@router.get("/{project_name}/info")
def route_project_info(
    project_name: str, project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler)
):
    return get_project_info(project_sqlite_db_handler, project_name=project_name)


@router.post("/add")
def route_add_project(
    project: Project, project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler)
):
    return add_project(project_db_handler=project_sqlite_db_handler, project=project)


@router.get("/{project_name}/remove")
def route_remove_project(
    project_name: str,
    project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler),
    deployed_models_sqlite_handler=Depends(get_deployed_models_sqlite_handler),
):
    return remove_project(project_sqlite_db_handler, deployed_models_sqlite_handler, project_name=project_name)
