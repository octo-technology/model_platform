"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

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
def list_models():
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
    return JSONResponse(
        content=[
            {
                "name": "model 1",
                "deployment_time_stamp": datetime.timestamp(datetime.now()),
                "version": 0,
                "uri": "https://get/a/prediction:8000/docs",
            }
        ],
        media_type="application/json",
    )
