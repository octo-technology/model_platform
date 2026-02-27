# Philippe Stepniewski
import inspect

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.model_info_usecases import search_model_infos
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project

router = APIRouter()


def get_model_info_db_handler(request: Request) -> ModelInfoDbHandler:
    return request.app.state.model_info_db_handler


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
