"""Use cases for agent_info synchronization and querying.

Mirrors the model_info_usecases pattern: a background sync reads agents from the
MLflow registry (filtered by `model_type=agent` tag) and populates the
AgentInfo DB. Compliance metadata (risk_level, act_review, etc.) is then
managed through the AgentInfoDbHandler.
"""

import json

from loguru import logger

from backend.domain.entities.agent_info import AgentInfo, AgentTool
from backend.domain.ports.agent_info_db_handler import AgentInfoDbHandler
from backend.domain.ports.agent_registry import AgentRegistry
from backend.infrastructure.agent_info_sqlite_db_handler import AgentInfoAlreadyExistError

RISK_LEVEL_MAPPING = {
    "inacceptable": "unacceptable",
    "élevé": "high",
    "eleve": "high",
    "limité": "limited",
    "limite": "limited",
    "minimal": "minimal",
    "unacceptable": "unacceptable",
    "high": "high",
    "limited": "limited",
}


def _extract_risk_level(tags: dict) -> str | None:
    raw = tags.get("ai_act_risk_level")
    if not raw:
        return None
    return RISK_LEVEL_MAPPING.get(raw.lower().strip(), raw.lower().strip())


def _parse_tools(tools_raw) -> list[AgentTool]:
    """Best-effort parse: tools may come as a list, a JSON string, or a comma-separated string."""
    if not tools_raw:
        return []
    if isinstance(tools_raw, list):
        return [AgentTool(**t) if isinstance(t, dict) else AgentTool(name=str(t)) for t in tools_raw]
    if isinstance(tools_raw, str):
        stripped = tools_raw.strip()
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                return _parse_tools(parsed)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse tools JSON tag: {stripped[:80]}")
        return [AgentTool(name=t.strip()) for t in stripped.split(",") if t.strip()]
    return []


def search_agent_infos(
    query: str,
    agent_info_db_handler: AgentInfoDbHandler,
    project_name: str | None = None,
) -> list[AgentInfo]:
    return agent_info_db_handler.search_agent_infos(query=query, project_name=project_name)


def sync_agent_infos_for_project(
    project_name: str,
    registry: AgentRegistry,
    agent_info_db_handler: AgentInfoDbHandler,
) -> None:
    agents = registry.list_all_agents()
    for agent in agents:
        versions = registry.list_agent_versions(agent["name"])
        for version_dict in versions:
            agent_version = str(version_dict["version"])
            agent_card = registry.get_agent_card(agent["name"], agent_version)

            registered_tags: dict = agent.get("tags") or {}
            risk_level = _extract_risk_level(registered_tags)
            try:
                agent_info_db_handler.add_agent_info(
                    AgentInfo(
                        agent_name=agent["name"],
                        agent_version=agent_version,
                        project_name=project_name,
                        description=registered_tags.get("description"),
                        agent_type=registered_tags.get("agent_type"),
                        llm_provider=registered_tags.get("llm_provider"),
                        llm_model=registered_tags.get("llm_model"),
                        guardrails=registered_tags.get("guardrails"),
                        max_iterations=(
                            int(registered_tags["max_iterations"])
                            if registered_tags.get("max_iterations", "").isdigit()
                            else None
                        ),
                        tools=_parse_tools(registered_tags.get("tools")),
                        agent_card=agent_card,
                        risk_level=risk_level,
                    )
                )
            except AgentInfoAlreadyExistError:
                # Refresh fields that may have changed
                if agent_card is not None:
                    agent_info_db_handler.update_agent_card(
                        agent_name=agent["name"],
                        agent_version=agent_version,
                        project_name=project_name,
                        agent_card=agent_card,
                    )
                if risk_level is not None:
                    agent_info_db_handler.update_risk_level(
                        agent_name=agent["name"],
                        agent_version=agent_version,
                        project_name=project_name,
                        risk_level=risk_level,
                    )
            except Exception as e:
                logger.warning(f"Could not upsert agent_info for {agent['name']}:{agent_version}: {e}")
