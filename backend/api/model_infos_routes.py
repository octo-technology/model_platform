# Philippe Stepniewski
import inspect

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.api.models_routes import get_project_registry_tracking_uri, get_registry_pool
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.model_registry import ModelRegistry
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases.ai_act_usecases import generate_ai_act_card
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.model_info_usecases import search_model_infos
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project

router = APIRouter()


def get_model_info_db_handler(request: Request) -> ModelInfoDbHandler:
    return request.app.state.model_info_db_handler


@router.get("/{project_name}/list")
def list_for_project(
    project_name: str,
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    infos = model_info_db_handler.list_model_infos_for_project(project_name)
    return JSONResponse(
        content=[
            {
                "model_name": i.model_name,
                "model_version": i.model_version,
                "has_generated_model_card": i.generated_model_card is not None,
                "act_review": i.act_review,
                "deterministic_compliance": i.deterministic_compliance or "not_evaluated",
                "llm_compliance": i.llm_compliance or "not_evaluated",
            }
            for i in infos
        ]
    )


@router.get("/{project_name}/{model_name}/{version}/ai_act_card")
def get_ai_act_card(
    project_name: str,
    model_name: str,
    version: str,
    request: Request,
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
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
    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    try:
        markdown = generate_ai_act_card(registry, model_info_db_handler, project_name, model_name, version)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(content={"markdown": markdown})


@router.get("/search")
def search(
    query: str,
    project_name: str | None = None,
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
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
    results = search_model_infos(query=query, model_info_db_handler=model_info_db_handler, project_name=project_name)
    return JSONResponse(content=[m.to_json() for m in results])
