"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from model_platform.domain.ports.model_registry import ModelRegistry
from model_platform.domain.use_cases.generate_and_build_image import generate_and_build_docker_image
from model_platform.infrastructure.mlflow_client_manager import MLFLOW_CLIENT
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter

router = APIRouter()

TASKS_STATUS = {}


def track_task_status(task_id: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Mettre à jour le statut en "in_progress"
                TASKS_STATUS[task_id] = "in_progress"
                # Exécuter la tâche
                result = func(*args, **kwargs)
                # Mettre à jour le statut en "completed"
                TASKS_STATUS[task_id] = "completed"
                return result
            except Exception as e:
                # Mettre le statut en "failed" en cas d'erreur
                TASKS_STATUS[task_id] = f"failed: {str(e)}"
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
async def route_deploy(
    model_name: str,
    version: str,
    background_tasks: BackgroundTasks,
    registry: ModelRegistry = Depends(get_model_registry),
):
    task_id = str(uuid.uuid4())
    TASKS_STATUS[task_id] = "queued"
    logging.info(f"Deploying {model_name}:{version} with task_id: {task_id}")
    decorated_task = track_task_status(task_id)(generate_and_build_docker_image)
    background_tasks.add_task(decorated_task, registry, model_name, version)

    return {"task_id": task_id, "status": "Deployment initiated"}


@router.get("/task-status/{task_id}")
async def check_task_status(task_id: str):
    status = TASKS_STATUS.get(task_id, "not_found")
    return {"task_id": task_id, "status": status}
