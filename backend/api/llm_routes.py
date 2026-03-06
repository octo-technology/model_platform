# Philippe Stepniewski
import inspect

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.api.models_routes import get_project_registry_tracking_uri, get_registry_pool
from backend.domain.entities.role import Role
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.model_registry import ModelRegistry
from backend.domain.ports.platform_config_handler import PlatformConfigHandler
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases import llm_usecases
from backend.domain.use_cases.ai_act_usecases import generate_ai_act_card
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.governance_usecases import extract_model_governance_information
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project
from backend.infrastructure.model_info_sqlite_db_handler import ModelInfoDoesntExistError

router = APIRouter()


def get_model_info_db_handler(request: Request) -> ModelInfoDbHandler:
    return request.app.state.model_info_db_handler


def get_platform_config_handler(request: Request) -> PlatformConfigHandler:
    return request.app.state.platform_config_handler


class ModelCardUpdateRequest(BaseModel):
    model_card: str


class AwsCredentialsRequest(BaseModel):
    access_key_id: str
    secret_access_key: str
    region: str = "us-east-1"


class AnthropicKeyRequest(BaseModel):
    api_key: str


class ProviderRequest(BaseModel):
    provider: str  # "bedrock" | "anthropic"


@router.get("/status")
def ai_status(
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Return whether the AI assist feature is available and the active provider."""
    return JSONResponse(
        content={
            "available": llm_usecases.is_available(platform_config_handler),
            "provider": llm_usecases.get_provider(platform_config_handler),
        }
    )


@router.put("/credentials")
def set_credentials(
    body: AwsCredentialsRequest,
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Store AWS Bedrock credentials in the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    platform_config_handler.set("AWS_ACCESS_KEY_ID", body.access_key_id)
    platform_config_handler.set("AWS_SECRET_ACCESS_KEY", body.secret_access_key)
    platform_config_handler.set("AWS_DEFAULT_REGION", body.region)
    return JSONResponse(content={"ok": True})


@router.delete("/credentials")
def delete_credentials(
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Remove AWS Bedrock credentials from the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    platform_config_handler.delete("AWS_ACCESS_KEY_ID")
    platform_config_handler.delete("AWS_SECRET_ACCESS_KEY")
    platform_config_handler.delete("AWS_DEFAULT_REGION")
    return JSONResponse(content={"ok": True})


@router.put("/provider")
def set_provider(
    body: ProviderRequest,
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Store the active LLM provider in the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    platform_config_handler.set("LLM_PROVIDER", body.provider)
    return JSONResponse(content={"ok": True})


@router.put("/api_key")
def set_api_key(
    body: AnthropicKeyRequest,
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Store the Anthropic API key in the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    platform_config_handler.set("ANTHROPIC_API_KEY", body.api_key)
    return JSONResponse(content={"ok": True})


@router.delete("/api_key")
def delete_api_key(
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Remove the Anthropic API key from the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    platform_config_handler.delete("ANTHROPIC_API_KEY")
    return JSONResponse(content={"ok": True})


@router.post("/{project_name}/{model_name}/{version}/model_card_suggest")
def model_card_suggest(
    project_name: str,
    model_name: str,
    version: str,
    request: Request,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
) -> JSONResponse:
    """Generate a model card suggestion using Claude based on governance metadata."""
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    if not llm_usecases.is_available(platform_config_handler):
        raise HTTPException(status_code=503, detail="AI assist is not available: no LLM provider configured.")

    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    try:
        governance_info = extract_model_governance_information(registry, project_name, model_name, version)
        # Flatten to include model_name and version in the info dict
        info = governance_info.get("model_information", {})
        if isinstance(info, dict):
            info["model_name"] = model_name
            info["version"] = version
        suggestion = llm_usecases.generate_model_card_suggestion(governance_info, project_name, platform_config_handler)
        model_info_db_handler.update_generated_model_card(model_name, version, project_name, suggestion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={"suggestion": suggestion})


@router.post("/{project_name}/{model_name}/{version}/act_review")
def act_review(
    project_name: str,
    model_name: str,
    version: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Review an AI Act compliance card using Claude and return structured remarks."""
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    if not llm_usecases.is_available(platform_config_handler):
        raise HTTPException(status_code=503, detail="AI assist is not available: no LLM provider configured.")

    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    try:
        ai_act_markdown = generate_ai_act_card(registry, model_info_db_handler, project_name, model_name, version)
        review = llm_usecases.review_ai_act_compliance(ai_act_markdown, platform_config_handler)
        model_info_db_handler.update_act_review(model_name, version, project_name, review)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={"review": review})


@router.get("/{project_name}/{model_name}/{version}/cached")
def get_cached(
    project_name: str,
    model_name: str,
    version: str,
    current_user: dict = Depends(get_current_user),
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
) -> JSONResponse:
    """Return cached AI generation state for a model version."""
    try:
        info = model_info_db_handler.get_model_info(model_name, version, project_name)
        return JSONResponse(
            content={
                "has_generated_model_card": info.generated_model_card is not None,
                "act_review": info.act_review,
            }
        )
    except ModelInfoDoesntExistError:
        return JSONResponse(content={"has_generated_model_card": False, "act_review": None})


@router.patch("/{project_name}/{model_name}/{version}/model_card")
def update_model_card(
    project_name: str,
    model_name: str,
    version: str,
    body: ModelCardUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
) -> JSONResponse:
    """Update the model card for a specific model version."""
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    try:
        updated = model_info_db_handler.update_model_card(
            model_name=model_name,
            model_version=version,
            project_name=project_name,
            model_card=body.model_card,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Model info not found.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={"ok": True})
