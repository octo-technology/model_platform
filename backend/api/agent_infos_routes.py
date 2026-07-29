"""Routes for agentic model compliance metadata.

Mirrors model_infos_routes.py but for agents. Agents themselves are registered
in MLflow with the `model_type=agent` tag; this module only exposes the
platform-side compliance metadata.
"""

import inspect

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.api.models_routes import get_project_registry_tracking_uri, get_registry_pool
from backend.domain.ports.agent_info_db_handler import AgentInfoDbHandler
from backend.domain.ports.agent_registry import AgentRegistry
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases.agent_ai_act_usecases import generate_agent_ai_act_card
from backend.domain.use_cases.agent_info_usecases import search_agent_infos
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project
from backend.infrastructure.agent_info_sqlite_db_handler import AgentInfoDoesntExistError

router = APIRouter()

VALID_RISK_LEVELS = {"unacceptable", "high", "limited", "minimal"}


def get_agent_info_db_handler(request: Request) -> AgentInfoDbHandler:
    return request.app.state.agent_info_db_handler


class AcceptRiskLevelRequest(BaseModel):
    risk_level: str


@router.get("/{project_name}/list")
def list_for_project(
    project_name: str,
    db_handler: AgentInfoDbHandler = Depends(get_agent_info_db_handler),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    agents = db_handler.list_agent_infos_for_project(project_name)
    return JSONResponse(content=[a.to_json() for a in agents])


@router.get("/{project_name}/{agent_name}/{agent_version}")
def get_agent_info(
    project_name: str,
    agent_name: str,
    agent_version: str,
    db_handler: AgentInfoDbHandler = Depends(get_agent_info_db_handler),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    try:
        agent = db_handler.get_agent_info(agent_name, agent_version, project_name)
    except AgentInfoDoesntExistError:
        raise HTTPException(status_code=404, detail="Agent not found")
    return JSONResponse(content=agent.to_json())


@router.get("/{project_name}/{agent_name}/{agent_version}/ai_act_card")
def get_ai_act_card(
    project_name: str,
    agent_name: str,
    agent_version: str,
    request: Request,
    db_handler: AgentInfoDbHandler = Depends(get_agent_info_db_handler),
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    agent_registry: AgentRegistry = registry_pool.get_agent_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    try:
        markdown = generate_agent_ai_act_card(agent_registry, db_handler, project_name, agent_name, agent_version)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(content={"markdown": markdown})


@router.post("/{project_name}/{agent_name}/{agent_version}/accept_risk_level")
def accept_risk_level(
    project_name: str,
    agent_name: str,
    agent_version: str,
    body: AcceptRiskLevelRequest,
    db_handler: AgentInfoDbHandler = Depends(get_agent_info_db_handler),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    level = body.risk_level.strip().lower()
    if level not in VALID_RISK_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid risk level: {body.risk_level}")
    db_handler.update_risk_level(agent_name, agent_version, project_name, level)
    return JSONResponse(content={"status": "ok", "risk_level": level})


@router.get("/search")
def search(
    query: str,
    project_name: str | None = None,
    db_handler: AgentInfoDbHandler = Depends(get_agent_info_db_handler),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    if project_name is not None:
        user_can_perform_action_for_project(
            current_user,
            project_name=project_name,
            action_name=inspect.currentframe().f_code.co_name,
            user_adapter=user_adapter,
        )
    results = search_agent_infos(query=query, agent_info_db_handler=db_handler, project_name=project_name)
    return JSONResponse(content=[a.to_json() for a in results])
