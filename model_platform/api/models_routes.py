"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse

from model_platform.domain.entities.docker.task_build_statuses import TaskBuildStatuses
from model_platform.domain.ports.model_registry import ModelRegistry
from model_platform.domain.ports.registry_handler import RegistryHandler
from model_platform.domain.use_cases.generate_and_build_image import generate_and_build_and_clean_docker_image
from model_platform.utils import sanitize_name

router = APIRouter()


def track_task_status(task_id: str, tasks_status: dict):
    """
    Decorator to track the status of a background task.

    Parameters
    ----------
    task_id : str
        The unique identifier for the task.

    Returns
    -------
    function
        A decorator function that wraps the target function to track its status.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            """
            Wrapper function to update the task status.

            Parameters
            ----------
            *args : tuple
                Positional arguments for the target function.
            **kwargs : dict
                Keyword arguments for the target function.

            Returns
            -------
            Any
                The result of the target function.

            Raises
            ------
            Exception
                If the target function raises an exception, it updates the task status to 'failed'.
            """
            try:
                tasks_status[task_id] = TaskBuildStatuses.in_progress
                result = func(*args, **kwargs)
                tasks_status[task_id] = TaskBuildStatuses.in_progress
                # Only works if in memory task tracker. In multiple runners, we need to retrieve the status from the
                # worker
                return result
            except Exception as e:
                tasks_status[task_id] = f"{TaskBuildStatuses.failed}: {str(e)}"
                raise

        return wrapper

    return decorator


def get_project_registry_tracking_uri(project_name: str, request: Request) -> str:
    tracking_uri: str = (
        "http://"
        + os.environ["MP_HOST_NAME"]
        + "/"
        + os.environ["MP_REGISTRY_PATH"]
        + "/"
        + sanitize_name(project_name)
    )
    logging.debug(f"Tracking URI: {tracking_uri} for {project_name}")
    return tracking_uri


def get_registry_pool(request: Request) -> RegistryHandler:
    """Dépendance qui fournit l'instance de REGISTRY_POOL depuis app.state."""
    return request.app.state.registry_pool


def get_tasks_status(request: Request) -> dict:
    return request.app.state.task_status


@router.get("/list")
def list_models(project_name: str, request: Request, registry_pool: RegistryHandler = Depends(get_registry_pool)):
    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    return JSONResponse(content=registry.list_all_models(), media_type="application/json")


@router.get("/{model_name}/versions")
def list_model_versions(
    project_name: str, model_name: str, request: Request, registry_pool: RegistryHandler = Depends(get_registry_pool)
):
    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    model_versions = registry.list_model_versions(model_name)
    return JSONResponse(content=model_versions, media_type="application/json")


@router.get("/deploy/{model_name}/{version}")
def route_deploy(
    project_name: str,
    model_name: str,
    version: str,
    request: Request,
    background_tasks: BackgroundTasks,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    tasks_status: dict = Depends(get_tasks_status),
):
    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = "queued"
    logging.info(f"Deploying {model_name}:{version} with task_id: {task_id}")
    decorated_task = track_task_status(task_id, tasks_status)(generate_and_build_and_clean_docker_image)
    background_tasks.add_task(decorated_task, registry, project_name, model_name, version)

    return {"task_id": task_id, "status": "Deployment initiated"}


@router.get("/task-status/{task_id}")
async def check_task_status(task_id: str, tasks_status: dict = Depends(get_tasks_status)):
    status = tasks_status.get(task_id, "not_found")
    return {"task_id": task_id, "status": status}
