"""Model Routes API module.

This module provides endpoints for interacting with the model registry.
"""

from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from model_platform.domain.use_cases.deployed_models import (
    list_deployed_models_with_status_for_a_project,
    remove_model_deployment_from_database,
)
from model_platform.infrastructure.log_model_deploy_sqlite_adapter import SQLiteLogModelDeployment

router = APIRouter()


def get_deployed_models_sqlite_handler(request: Request) -> SQLiteLogModelDeployment:
    return request.app.state.deployed_models_db


@router.get("/list")
def list_models(
    project_name: str, deployed_models_sqlite_handler=Depends(get_deployed_models_sqlite_handler)
) -> JSONResponse:
    deployed_models = list_deployed_models_with_status_for_a_project(project_name, deployed_models_sqlite_handler)
    return JSONResponse(deployed_models, media_type="application/json")


@router.get("/remove/{model_name}/{version}")
def remove_model_deployment_from_db(
    project_name: str,
    model_name: str,
    version: str,
    deployed_models_sqlite_handler=Depends(get_deployed_models_sqlite_handler),
) -> JSONResponse:
    status = remove_model_deployment_from_database(deployed_models_sqlite_handler, project_name, model_name, version)
    return JSONResponse({"status": status}, media_type="application/json")
