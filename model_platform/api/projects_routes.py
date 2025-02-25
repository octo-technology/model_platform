from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from model_platform.domain.entities.project import Project
from model_platform.domain.use_cases.projects_usecases import (
    EVENT_LOGGER,
    add_project,
    get_project_info,
    list_projects,
    remove_project,
)
from model_platform.infrastructure.project_sqlite_db_handler import ProjectSQLiteDBHandler

router = APIRouter()


def get_project_sqlite_db_handler(request: Request):
    return request.app.state.project_sqlite_db_handler


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
) -> JSONResponse:
    status = add_project(project_db_handler=project_sqlite_db_handler, project=project)
    return JSONResponse({"status": status}, media_type="application/json")


@router.get("/{project_name}/remove")
def route_remove_project(
    project_name: str,
    project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler),
):
    return remove_project(project_sqlite_db_handler, project_name=project_name)


@router.get("/{project_name}/governance")
def route_project_governance(project_name: str):
    return EVENT_LOGGER.list_events(project_name)
