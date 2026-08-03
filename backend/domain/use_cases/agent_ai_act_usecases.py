from datetime import datetime, timezone
from pathlib import Path

from backend.domain.entities.agent_info import AgentInfo, AgentTool
from backend.domain.ports.agent_info_db_handler import AgentInfoDbHandler
from backend.domain.ports.agent_registry import AgentRegistry
from backend.domain.use_cases.ai_act_usecases import _risk_level_checkboxes
from backend.infrastructure.agent_info_sqlite_db_handler import AgentInfoDoesntExistError

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "agent_ai_act_card.md"


def _load_template() -> str:
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def _tools_table(tools: list[AgentTool]) -> str:
    if not tools:
        return "*Aucun outil déclaré.*"
    rows = "\n".join(f"| `{t.name}` | {t.description or '*à compléter*'} |" for t in tools)
    return f"| Outil | Description |\n|---|---|\n{rows}"


def _guardrails_block(guardrails: str | None) -> str:
    if not guardrails:
        return "*Aucun garde-fou déclaré.*"
    return f"```\n{guardrails}\n```"


def _max_iterations_statement(max_iterations: int | None) -> str:
    if max_iterations is None:
        return "*à compléter — aucune limite d'itérations déclarée*"
    return f"oui — {max_iterations} itérations maximum par requête"


def generate_agent_ai_act_card(
    agent_registry: AgentRegistry,
    agent_info_db_handler: AgentInfoDbHandler,
    project_name: str,
    agent_name: str,
    version: str,
) -> str:
    """Generate a Markdown AI Act compliance card for an agent version."""
    governance = agent_registry.get_agent_governance_information(agent_name, version)
    run_id: str = governance.get("run_id") or "N/A"
    # Run tags take precedence over registered-model tags (per-version wins)
    tags: dict = {**governance.get("registered_model_tags", {}), **governance.get("run_tags", {})}

    try:
        agent_info: AgentInfo | None = agent_info_db_handler.get_agent_info(agent_name, version, project_name)
    except AgentInfoDoesntExistError:
        agent_info = None

    def info(attr: str):
        return getattr(agent_info, attr, None) if agent_info else None

    context = {
        "agent_name": agent_name,
        "version": version,
        "project_name": project_name,
        "run_id": run_id,
        "user": tags.get("mlflow.user", "*à compléter*"),
        "risk_level_checkboxes": _risk_level_checkboxes(info("risk_level")),
        "description": info("description")
        or tags.get("description")
        or tags.get("mlflow.note.content")
        or "*à compléter*",
        "agent_type": info("agent_type") or tags.get("agent_type") or "*à compléter*",
        "framework": tags.get("framework", "*à compléter*"),
        "llm_provider": info("llm_provider") or tags.get("llm_provider") or "*à compléter*",
        "llm_model": info("llm_model") or tags.get("llm_model") or "*à compléter*",
        "max_iterations": info("max_iterations") if info("max_iterations") is not None else "*à compléter*",
        "max_iterations_statement": _max_iterations_statement(info("max_iterations")),
        "tools_table": _tools_table(info("tools") or []),
        "guardrails_block": _guardrails_block(info("guardrails")),
        "data_source": tags.get("data_source", "*à compléter*"),
        "data_language": tags.get("data_language", "*à compléter*"),
        "now_str": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    return _load_template().format_map(context)
