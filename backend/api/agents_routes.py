"""Agent deploy/undeploy routes.

Mirrors models_routes.py but for agents. Uses the existing task-tracking and
registry-pool dependencies.
"""

import inspect
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger

from backend.api.models_routes import (
    get_dashboard_handler,
    get_project_registry_tracking_uri,
    get_registry_pool,
    get_tasks_status,
    track_task_status,
)
from backend.domain.entities.docker.task_build_statuses import TaskBuildStatuses
from backend.domain.ports.dashboard_handler import DashboardHandler
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.deploy_agent import deploy_agent, remove_agent_deployment
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project

router = APIRouter()


@router.get("/list")
def list_agents(
    project_name: str,
    request: Request,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    """Return agents from the project's MLflow registry (model_type=agent tagged).

    Includes creation_timestamp, aliases, tags, latest_versions — same shape as
    /{project}/models/list but for agents only.
    """
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    agent_registry = registry_pool.get_agent_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    return JSONResponse(content=agent_registry.list_all_agents(), media_type="application/json")


@router.get("/{agent_name}/versions")
def list_agent_versions(
    project_name: str,
    agent_name: str,
    request: Request,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    agent_registry = registry_pool.get_agent_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    return JSONResponse(content=agent_registry.list_agent_versions(agent_name), media_type="application/json")


@router.get("/deploy/{agent_name}/{version}")
def route_deploy_agent(
    project_name: str,
    agent_name: str,
    version: str,
    request: Request,
    background_tasks: BackgroundTasks,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    tasks_status: dict = Depends(get_tasks_status),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
    dashboard_handler: DashboardHandler = Depends(get_dashboard_handler),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )

    # Reuse the ML model registry adapter — it serves the same MLflow that
    # holds the agents, and build_model_docker_image uses generic pyfunc loading
    registry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = "queued"
    logger.debug(f"Deploying agent {agent_name}:{version} with task_id: {task_id}")
    decorated_task = track_task_status(task_id, tasks_status)(deploy_agent)
    background_tasks.add_task(
        decorated_task, registry, project_name, agent_name, version, dashboard_handler, current_user["email"]
    )
    return JSONResponse({"task_id": task_id, "status": "Agent deployment initiated"}, media_type="application/json")


@router.get("/undeploy/{agent_name}/{version}")
def route_undeploy_agent(
    project_name: str,
    agent_name: str,
    version: str,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
    dashboard_handler: DashboardHandler = Depends(get_dashboard_handler),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    return_code = remove_agent_deployment(project_name, agent_name, version, dashboard_handler, current_user["email"])
    return JSONResponse({"return_code": return_code}, media_type="application/json")


@router.get("/task-status/{task_id}")
async def check_task_status(
    task_id: str,
    project_name: str,
    tasks_status: dict = Depends(get_tasks_status),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    status = tasks_status.get(task_id, TaskBuildStatuses.failed)
    return JSONResponse({"task_id": task_id, "status": status}, media_type="application/json")
