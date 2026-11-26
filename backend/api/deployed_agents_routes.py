"""Deployed agents list endpoint. Mirrors deployed_models_routes.py."""

import inspect

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.deployed_agents import list_deployed_agents_with_status_for_a_project
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project

router = APIRouter()


@router.get("/list")
def list_deployed_agents(
    project_name: str,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    return JSONResponse(list_deployed_agents_with_status_for_a_project(project_name), media_type="application/json")
