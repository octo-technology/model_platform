"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from model_platform.domain.ports.model_registry import ModelRegistry
from model_platform.domain.use_cases.generate_and_build_image import generate_and_build_docker_image
from model_platform.infrastructure.mlflow_client_manager import MLFLOW_CLIENT
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter

router = APIRouter()


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


@router.post("/deploy/{model_name}/{version}")
def route_deploy(model_name: str, version: str, registry: ModelRegistry = Depends(get_model_registry)):
    logging.info(f"Deploying {model_name}")
    generate_and_build_docker_image(registry, model_name, version)
