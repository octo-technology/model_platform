# Philippe Stepniewski
import inspect
import os

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
from backend.domain.use_cases.compliance_usecases import extract_llm_compliance_from_review
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project

router = APIRouter()


def get_model_info_db_handler(request: Request) -> ModelInfoDbHandler:
    return request.app.state.model_info_db_handler


def get_platform_config_handler(request: Request) -> PlatformConfigHandler:
    return request.app.state.platform_config_handler


class BedrockApiKeyRequest(BaseModel):
    api_key: str
    region: str = "eu-west-3"


class AnthropicKeyRequest(BaseModel):
    api_key: str


class ProviderRequest(BaseModel):
    provider: str  # "bedrock" | "anthropic"


class BedrockModelRequest(BaseModel):
    model_id: str


@router.get("/status")
def ai_status(
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Return whether the AI assist feature is available and the active provider."""
    provider = llm_usecases.get_provider(platform_config_handler)
    result = {
        "available": llm_usecases.is_available(platform_config_handler),
        "provider": provider,
    }
    if provider == "bedrock":
        result["bedrock_model_id"] = llm_usecases.get_bedrock_model_id(platform_config_handler)
        result["bedrock_models"] = llm_usecases.BEDROCK_MODELS
    return JSONResponse(content=result)


@router.put("/credentials")
def set_credentials(
    body: BedrockApiKeyRequest,
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Store Bedrock API key (bearer token) in the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    platform_config_handler.set("AWS_BEARER_TOKEN_BEDROCK", body.api_key)
    platform_config_handler.set("AWS_DEFAULT_REGION", body.region)
    return JSONResponse(content={"ok": True})


@router.delete("/credentials")
def delete_credentials(
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Remove Bedrock API key from the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    platform_config_handler.delete("AWS_BEARER_TOKEN_BEDROCK")
    platform_config_handler.delete("AWS_DEFAULT_REGION")
    os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)
    os.environ.pop("AWS_DEFAULT_REGION", None)
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


@router.put("/model")
def set_model(
    body: BedrockModelRequest,
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Store the selected Bedrock model ID in the platform config. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    if body.model_id not in llm_usecases.BEDROCK_MODELS:
        raise HTTPException(status_code=400, detail="Invalid model ID.")
    platform_config_handler.set("BEDROCK_MODEL_ID", body.model_id)
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
    os.environ.pop("ANTHROPIC_API_KEY", None)
    return JSONResponse(content={"ok": True})


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
        llm_status = extract_llm_compliance_from_review(review)
        model_info_db_handler.update_compliance_statuses(
            model_name=model_name,
            model_version=version,
            project_name=project_name,
            llm_compliance=llm_status,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content={"review": review, "llm_compliance": llm_status})


@router.post("/{project_name}/{model_name}/{version}/suggest_risk_level")
def suggest_risk_level(
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
    """Suggest an AI Act risk level for a model version using Claude."""
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
        result = llm_usecases.suggest_risk_level(ai_act_markdown, platform_config_handler)
        if result["suggested_risk_level"]:
            model_info_db_handler.update_suggested_risk_level(
                model_name, version, project_name, result["suggested_risk_level"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(content=result)


class GatePolicyRequest(BaseModel):
    policy: str  # "strict" | "permissive" | "disabled"


@router.get("/gate_policy")
def get_gate_policy(
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Return the current deployment gate policy."""
    policy = platform_config_handler.get("DEPLOYMENT_GATE_POLICY") or "permissive"
    return JSONResponse(content={"policy": policy})


@router.put("/gate_policy")
def set_gate_policy(
    body: GatePolicyRequest,
    current_user: dict = Depends(get_current_user),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> JSONResponse:
    """Set the deployment gate policy. Admin only."""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    if body.policy not in ("strict", "permissive", "disabled"):
        raise HTTPException(status_code=400, detail="Invalid policy. Must be strict, permissive, or disabled.")
    platform_config_handler.set("DEPLOYMENT_GATE_POLICY", body.policy)
    return JSONResponse(content={"ok": True})
