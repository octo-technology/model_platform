"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from model_platform.domain.use_cases.deployed_models import (
    list_deployed_models_with_status_for_a_project,
)
from model_platform.api.auth import get_current_user

router = APIRouter()


@router.get("/list")
def list_models(
    project_name: str,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    deployed_models = list_deployed_models_with_status_for_a_project(project_name)
    return JSONResponse(deployed_models, media_type="application/json")
