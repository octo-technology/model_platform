"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

from fastapi import APIRouter, Depends, Request

from model_platform.domain.use_cases.deployed_models import list_deployed_models_with_status_for_a_project
from model_platform.infrastructure.log_model_deploy_sqlite_adapter import SQLiteLogModelDeployment

router = APIRouter()


def get_deployed_models_sqlite_handler(request: Request) -> SQLiteLogModelDeployment:
    return request.app.state.deployed_models_db


@router.get("/list")
def list_models(project_name: str, deployed_models_sqlite_handler=Depends(get_deployed_models_sqlite_handler)):
    deployed_models = list_deployed_models_with_status_for_a_project(project_name, deployed_models_sqlite_handler)
    return deployed_models
