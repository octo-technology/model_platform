"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

from fastapi import APIRouter, Depends

from model_platform.adapters.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter
from model_platform.domain.ports.model_registry import ModelRegistry

router = APIRouter()


def get_model_registry():
    """Dependency that provides an instance of the MLFlowModelRegistryAdapter.

    Returns
    -------
    MLFlowModelRegistryAdapter
        An instance of the MLFlowModelRegistryAdapter.
    """
    return MLFlowModelRegistryAdapter()


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
    return registry.list_all_models()
