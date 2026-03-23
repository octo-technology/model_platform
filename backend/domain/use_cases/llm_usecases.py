# Philippe Stepniewski
import json
import os
from pathlib import Path

import anthropic
import boto3
from loguru import logger

from backend.domain.ports.platform_config_handler import PlatformConfigHandler

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load_prompt(filename: str) -> str:
    return (_TEMPLATES_DIR / filename).read_text(encoding="utf-8")


BEDROCK_MODELS = {
    "eu.anthropic.claude-sonnet-4-20250514-v1:0": "Claude Sonnet 4",
    "eu.anthropic.claude-haiku-4-5-20251001-v1:0": "Claude Haiku 4.5",
    "eu.anthropic.claude-3-5-sonnet-20241022-v2:0": "Claude 3.5 Sonnet v2",
    "eu.anthropic.claude-3-5-haiku-20241022-v1:0": "Claude 3.5 Haiku",
}
BEDROCK_DEFAULT_MODEL_ID = "eu.anthropic.claude-sonnet-4-20250514-v1:0"
ANTHROPIC_MODEL_ID = "claude-sonnet-4-20250514"


def get_bedrock_api_key(platform_config_handler: PlatformConfigHandler = None) -> str | None:
    """Returns the Bedrock bearer token (API key) or None if not configured."""
    api_key = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
    if api_key:
        return api_key
    if platform_config_handler is not None:
        api_key = platform_config_handler.get("AWS_BEARER_TOKEN_BEDROCK")
        if api_key:
            return api_key
    return None


def get_bedrock_region(platform_config_handler: PlatformConfigHandler = None) -> str:
    """Returns the AWS region for Bedrock, defaulting to eu-west-3."""
    region = os.environ.get("AWS_DEFAULT_REGION")
    if region:
        return region
    if platform_config_handler is not None:
        region = platform_config_handler.get("AWS_DEFAULT_REGION")
        if region:
            return region
    return "eu-west-3"


def get_bedrock_model_id(platform_config_handler: PlatformConfigHandler = None) -> str:
    """Returns the selected Bedrock model ID, defaulting to Claude Sonnet 4."""
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    if model_id:
        return model_id
    if platform_config_handler is not None:
        model_id = platform_config_handler.get("BEDROCK_MODEL_ID")
        if model_id:
            return model_id
    return BEDROCK_DEFAULT_MODEL_ID


def get_anthropic_api_key(platform_config_handler: PlatformConfigHandler = None) -> str | None:
    """Returns Anthropic API key or None if not configured."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return api_key
    if platform_config_handler is not None:
        api_key = platform_config_handler.get("ANTHROPIC_API_KEY")
        if api_key:
            return api_key
    return None


def get_provider(platform_config_handler: PlatformConfigHandler = None) -> str | None:
    """Returns the active LLM provider: 'bedrock', 'anthropic', or None."""
    provider = os.environ.get("LLM_PROVIDER")
    if provider:
        return provider
    if platform_config_handler is not None:
        provider = platform_config_handler.get("LLM_PROVIDER")
        if provider:
            return provider
    return None


def _make_client(platform_config_handler: PlatformConfigHandler = None):
    provider = get_provider(platform_config_handler)
    if provider == "anthropic":
        return anthropic.Anthropic(api_key=get_anthropic_api_key(platform_config_handler))
    # Bedrock: use boto3 with bearer token auth
    api_key = get_bedrock_api_key(platform_config_handler)
    region = get_bedrock_region(platform_config_handler)
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key or ""
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        endpoint_url=f"https://bedrock-runtime.{region}.amazonaws.com",
    )


def is_available(platform_config_handler: PlatformConfigHandler = None) -> bool:
    """Return True if the configured LLM provider has credentials."""
    provider = get_provider(platform_config_handler)
    if provider == "bedrock":
        return get_bedrock_api_key(platform_config_handler) is not None
    if provider == "anthropic":
        return get_anthropic_api_key(platform_config_handler) is not None
    return False


def _call_bedrock(client, model_id: str, prompt: str, max_tokens: int) -> str:
    """Call Bedrock converse API and return the text response."""
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens},
    )
    output_message = response["output"]["message"]
    return next((block["text"] for block in output_message["content"] if "text" in block), "")


def review_ai_act_compliance(ai_act_card_markdown: str, platform_config_handler: PlatformConfigHandler = None) -> str:
    """
    Call Claude to review an AI Act compliance card and return structured remarks.
    Returns a markdown-formatted review.
    """
    client = _make_client(platform_config_handler)
    provider = get_provider(platform_config_handler)
    model_id = ANTHROPIC_MODEL_ID if provider == "anthropic" else get_bedrock_model_id(platform_config_handler)

    prompt = _load_prompt("ai_act_review.txt").format(ai_act_card_markdown=ai_act_card_markdown)

    if provider == "anthropic":
        with client.messages.stream(
            model=model_id,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = stream.get_final_message()
        return next((b.text for b in message.content if b.type == "text"), "")

    return _call_bedrock(client, model_id, prompt, max_tokens=4096)


VALID_RISK_LEVELS = {"unacceptable", "high", "limited", "minimal"}


def suggest_risk_level(ai_act_card_markdown: str, platform_config_handler: PlatformConfigHandler = None) -> dict:
    """
    Call Claude to suggest an AI Act risk level based on the model's AI Act card.
    Returns {"suggested_risk_level": "high", "justification": "..."}.
    """
    client = _make_client(platform_config_handler)
    provider = get_provider(platform_config_handler)
    model_id = ANTHROPIC_MODEL_ID if provider == "anthropic" else get_bedrock_model_id(platform_config_handler)

    prompt = _load_prompt("risk_level_suggestion.txt").format(ai_act_card_markdown=ai_act_card_markdown)

    if provider == "anthropic":
        with client.messages.stream(
            model=model_id,
            max_tokens=1024,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = stream.get_final_message()
        raw_response = next((b.text for b in message.content if b.type == "text"), "")
    else:
        raw_response = _call_bedrock(client, model_id, prompt, max_tokens=1024)

    return _parse_risk_level_response(raw_response)


def _parse_risk_level_response(raw_response: str) -> dict:
    """Extract the suggested risk level and justification from LLM JSON response."""
    cleaned = raw_response.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse risk level suggestion as JSON: {raw_response[:200]}")
        return {"suggested_risk_level": None, "justification": raw_response}

    level = result.get("suggested_risk_level", "").lower().strip()
    if level not in VALID_RISK_LEVELS:
        logger.warning(f"LLM suggested invalid risk level: {level}")
        return {"suggested_risk_level": None, "justification": result.get("justification", raw_response)}

    return {"suggested_risk_level": level, "justification": result.get("justification", "")}
