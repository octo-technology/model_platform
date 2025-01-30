"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse

from model_platform.domain.entities.docker.task_build_statuses import TaskBuildStatuses
from model_platform.domain.ports.model_registry import ModelRegistry
from model_platform.domain.ports.registry_handler import RegistryHandler
from model_platform.domain.use_cases.generate_and_build_image import generate_and_build_and_clean_docker_image

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
                return result
            except Exception as e:
                tasks_status[task_id] = f"{TaskBuildStatuses.failed}: {str(e)}"
                raise

        return wrapper

    return decorator


def get_project_registry_connexion_params(project_name: str) -> dict[str:str]:
    return {"project_name": project_name, "tracking_uri": "http://127.0.0.1:5000"}


def get_registry_pool(request: Request) -> RegistryHandler:
    """Dépendance qui fournit l'instance de REGISTRY_POOL depuis app.state."""
    return request.app.state.registry_pool


def get_tasks_status(request: Request) -> dict:
    return request.app.state.task_status


@router.get("/list")
def list_models(registry_pool: RegistryHandler = Depends(get_registry_pool), project_name: str = None):
    registry: ModelRegistry = registry_pool.connect(get_project_registry_connexion_params(project_name))
    return JSONResponse(content=registry.list_all_models(), media_type="application/json")


@router.get("/{model_name}/versions")
def list_model_versions(
    registry_pool: RegistryHandler = Depends(get_registry_pool), project_name: str = None, model_name: str = None
):
    registry: ModelRegistry = registry_pool.connect(get_project_registry_connexion_params(project_name))
    model_versions = registry.list_model_versions(model_name)
    return JSONResponse(content=model_versions, media_type="application/json")


@router.get("/deploy/{model_name}/{version}")
def route_deploy(
    background_tasks: BackgroundTasks,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    tasks_status: dict = Depends(get_tasks_status),
    project_name: str = None,
    model_name: str = None,
    version: str = None,
):
    registry: ModelRegistry = registry_pool.connect(get_project_registry_connexion_params(project_name))
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = "queued"
    logging.info(f"Deploying {model_name}:{version} with task_id: {task_id}")
    decorated_task = track_task_status(task_id, tasks_status)(generate_and_build_and_clean_docker_image)
    background_tasks.add_task(decorated_task, registry, model_name, version)

    return {"task_id": task_id, "status": "Deployment initiated"}


@router.get("/task-status/{task_id}")
async def check_task_status(task_id: str, tasks_status: dict = Depends(get_tasks_status)):
    status = tasks_status.get(task_id, "not_found")
    return {"task_id": task_id, "status": status}
