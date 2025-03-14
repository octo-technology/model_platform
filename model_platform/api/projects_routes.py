import inspect

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import FileResponse, JSONResponse

from model_platform.api.models_routes import get_project_registry_tracking_uri, get_registry_pool
from model_platform.domain.entities.project import Project
from model_platform.domain.entities.role import Role
from model_platform.domain.ports.model_registry import ModelRegistry
from model_platform.domain.ports.registry_handler import RegistryHandler
from model_platform.domain.ports.user_handler import UserHandler
from model_platform.domain.use_cases import user_usecases
from model_platform.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from model_platform.domain.use_cases.governance_usecases import (
    download_project_models_governance_information,
    return_project_models_governance_information,
)
from model_platform.domain.use_cases.projects_usecases import (
    add_project,
    get_project_info,
    list_projects,
    list_projects_for_user,
    remove_project,
)
from model_platform.domain.use_cases.user_usecases import user_can_perform_action_for_project
from model_platform.infrastructure.project_sqlite_db_handler import ProjectSQLiteDBHandler

router = APIRouter()


def get_project_sqlite_db_handler(request: Request):
    return request.app.state.project_sqlite_db_handler


@router.get("/list")
def route_list_projects(
    project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] == Role.ADMIN:
        return list_projects(project_db_handler=project_sqlite_db_handler)
    else:
        return list_projects_for_user(current_user["email"], project_db_handler=project_sqlite_db_handler)


@router.get("/{project_name}/info")
def route_project_info(
    project_name: str,
    project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    return get_project_info(project_sqlite_db_handler, project_name=project_name)


@router.post("/add")
def route_add_project(
    project: Project,
    project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user, project_name="", action_name=inspect.currentframe().f_code.co_name, user_adapter=user_adapter
    )
    status = add_project(project_db_handler=project_sqlite_db_handler, project=project)
    return JSONResponse(content={"status": status}, media_type="application/json")


@router.get("/{project_name}/remove")
def route_remove_project(
    project_name: str,
    project_sqlite_db_handler: ProjectSQLiteDBHandler = Depends(get_project_sqlite_db_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user, project_name="", action_name=inspect.currentframe().f_code.co_name, user_adapter=user_adapter
    )
    return remove_project(project_sqlite_db_handler, project_name=project_name)


@router.post("/{project_name}/add_user")
def route_add_user_to_project(
    project_name: str,
    email: str,
    role: str,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    success = user_usecases.add_user_to_project(
        user_adapter=user_adapter, project_name=project_name, email=email, role=role
    )
    if success:
        return JSONResponse(content={"status": success}, media_type="application/json")
    else:
        raise HTTPException(status_code=403, detail="Unexpected error has occurred")


@router.get("/{project_name}/download_governance")
def download_governance_route(
    project_name: str,
    request: Request,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> FileResponse:
    if current_user["role"] != Role.ADMIN:
        user_can_perform_action_for_project(
            current_user,
            project_name=project_name,
            action_name=inspect.currentframe().f_code.co_name,
            user_adapter=user_adapter,
        )
    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    zip_path = download_project_models_governance_information(project_name, registry)

    return FileResponse(zip_path, media_type="application/zip", filename=f"{project_name + 'governance'}.zip")


@router.get("/{project_name}/governance")
def governance_route(
    project_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    user_adapter: UserHandler = Depends(get_user_adapter),
):
    if current_user["role"] != Role.ADMIN:
        user_can_perform_action_for_project(
            current_user,
            project_name=project_name,
            action_name=inspect.currentframe().f_code.co_name,
            user_adapter=user_adapter,
        )
    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    project_governance = return_project_models_governance_information(project_name, registry)
    return JSONResponse(content={"project_gouvernance": project_governance}, media_type="application/json")


@router.get("/{project_name}/users")
def get_users_for_project(
    project_name: str,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    users = user_usecases.get_users_for_project(project_name, user_adapter)
    return JSONResponse(content={"users": users}, media_type="application/json")


@router.post("/{project_name}/remove_user")
def route_remove_user_from_project(
    project_name: str,
    email: str,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    success = user_usecases.remove_user_from_project(user_adapter, email, project_name)
    return JSONResponse(content={"status": success}, media_type="application/json")


@router.post("/{project_name}/change_user_role")
def route_change_user_role_for_project(
    project_name: str,
    email: str,
    role: str,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    success = user_usecases.change_user_role_for_project(email, project_name, role, user_adapter)
    return JSONResponse(content={"status": success}, media_type="application/json")
