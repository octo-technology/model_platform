# Philippe Stepniewski
import os
from pathlib import Path

import anthropic
from anthropic import AnthropicBedrock

from backend.domain.ports.platform_config_handler import PlatformConfigHandler

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load_prompt(filename: str) -> str:
    return (_TEMPLATES_DIR / filename).read_text(encoding="utf-8")


BEDROCK_MODEL_ID = "us.anthropic.claude-opus-4-5-20250514-v1:0"
ANTHROPIC_MODEL_ID = "claude-opus-4-6"


def get_aws_credentials(platform_config_handler: PlatformConfigHandler = None) -> dict | None:
    """Returns AWS credentials dict or None if not configured."""
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    if access_key and secret_key:
        return {"access_key": access_key, "secret_key": secret_key, "region": region}
    if platform_config_handler is not None:
        access_key = platform_config_handler.get("AWS_ACCESS_KEY_ID")
        secret_key = platform_config_handler.get("AWS_SECRET_ACCESS_KEY")
        region = platform_config_handler.get("AWS_DEFAULT_REGION") or "us-east-1"
        if access_key and secret_key:
            return {"access_key": access_key, "secret_key": secret_key, "region": region}
    return None


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
    # Default: Bedrock
    creds = get_aws_credentials(platform_config_handler)
    if creds:
        return AnthropicBedrock(
            aws_access_key=creds["access_key"],
            aws_secret_key=creds["secret_key"],
            aws_region=creds["region"],
        )
    # Fallback: let boto3 default credential chain handle it (IRSA, instance metadata, etc.)
    return AnthropicBedrock(aws_region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))


def is_available(platform_config_handler: PlatformConfigHandler = None) -> bool:
    """Return True if the configured LLM provider has credentials."""
    provider = get_provider(platform_config_handler)
    if provider == "bedrock":
        return get_aws_credentials(platform_config_handler) is not None
    if provider == "anthropic":
        return get_anthropic_api_key(platform_config_handler) is not None
    return False


def generate_model_card_suggestion(
    governance_info: dict, project_name: str, platform_config_handler: PlatformConfigHandler = None
) -> str:
    """
    Call Claude to draft a model card based on governance metadata.
    Returns the generated markdown text.
    """
    client = _make_client(platform_config_handler)
    provider = get_provider(platform_config_handler)
    model_id = ANTHROPIC_MODEL_ID if provider == "anthropic" else BEDROCK_MODEL_ID

    info = governance_info.get("model_information", governance_info)
    tags = info.get("tags", {})
    params = info.get("params", {})
    metrics = info.get("metrics", {})
    model_name = info.get("model_name", "unknown")
    version = info.get("version", "?")

    context_lines = [
        f"Project: {project_name}",
        f"Model name: {model_name}",
        f"Version: {version}",
        f"Run name: {tags.get('mlflow.runName', 'N/A')}",
        f"Author: {tags.get('mlflow.user', 'N/A')}",
    ]
    if params:
        context_lines.append("Hyperparameters: " + ", ".join(f"{k}={v}" for k, v in params.items()))
    if metrics:
        context_lines.append("Metrics: " + ", ".join(f"{k}={v}" for k, v in metrics.items()))

    existing_note = tags.get("mlflow.note.content")
    if existing_note:
        context_lines.append(f"Existing description: {existing_note}")

    context_text = "\n".join(context_lines)

    prompt = _load_prompt("model_card_suggest.txt").format(context_text=context_text)

    with client.messages.stream(
        model=model_id,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()

    return next((b.text for b in message.content if b.type == "text"), "")


def review_ai_act_compliance(ai_act_card_markdown: str, platform_config_handler: PlatformConfigHandler = None) -> str:
    """
    Call Claude to review an AI Act compliance card and return structured remarks.
    Returns a markdown-formatted review.
    """
    client = _make_client(platform_config_handler)
    provider = get_provider(platform_config_handler)
    model_id = ANTHROPIC_MODEL_ID if provider == "anthropic" else BEDROCK_MODEL_ID

    prompt = _load_prompt("ai_act_review.txt").format(ai_act_card_markdown=ai_act_card_markdown)

    with client.messages.stream(
        model=model_id,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()

    return next((b.text for b in message.content if b.type == "text"), "")
