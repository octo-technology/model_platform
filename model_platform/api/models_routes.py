"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from model_platform.domain.entities.docker.task_build_statuses import TaskBuildStatuses
from model_platform.domain.ports.model_registry import ModelRegistry
from model_platform.domain.use_cases.generate_and_build_image import generate_and_build_and_clean_docker_image
from model_platform.infrastructure.mlflow_client_manager import MLFLOW_CLIENT
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter

router = APIRouter()

TASKS_STATUS = {}


def track_task_status(task_id: str):
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
                TASKS_STATUS[task_id] = TaskBuildStatuses.in_progress
                result = func(*args, **kwargs)
                TASKS_STATUS[task_id] = TaskBuildStatuses.in_progress
                return result
            except Exception as e:
                TASKS_STATUS[task_id] = f"{TaskBuildStatuses.failed}: {str(e)}"
                raise

        return wrapper

    return decorator


def get_model_registry():
    """Dependency that provides an instance of the MLFlowModelRegistryAdapter.

    Returns
    -------
    MLFlowModelRegistryAdapter
        An instance of the MLFlowModelRegistryAdapter.
    """
    return MLFlowModelRegistryAdapter(MLFLOW_CLIENT.client)


@router.get("/list")
def list_models(registry: ModelRegistry = Depends(get_model_registry)):
    """Endpoint to list all registered models.

    Parameters
    ----------
    registry : ModelRegistry, optional
        The model registry adapter, by default Depends(get_model_registry)

    Returns
    -------
    list[dict[str, str | int]]
        A list of dictionaries containing model attributes.
    """
    return JSONResponse(content=registry.list_all_models(), media_type="application/json")


@router.get("/deploy/{model_name}/{version}")
def route_deploy(
    model_name: str,
    version: str,
    background_tasks: BackgroundTasks,
    registry: ModelRegistry = Depends(get_model_registry),
):
    task_id = str(uuid.uuid4())
    TASKS_STATUS[task_id] = "queued"
    logging.info(f"Deploying {model_name}:{version} with task_id: {task_id}")
    decorated_task = track_task_status(task_id)(generate_and_build_and_clean_docker_image)
    background_tasks.add_task(decorated_task, registry, model_name, version)

    return {"task_id": task_id, "status": "Deployment initiated"}


@router.get("/task-status/{task_id}")
async def check_task_status(task_id: str):
    status = TASKS_STATUS.get(task_id, "not_found")
    return {"task_id": task_id, "status": status}
