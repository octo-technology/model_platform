"""Agent Registry Port module.

Abstract interface for listing and inspecting agentic models registered in
the project's model registry (currently MLflow). Agents are distinguished
from ML models by the `model_type=agent` registered-model tag.
"""

from abc import ABC, abstractmethod


class AgentRegistry(ABC):
    """Abstract base class for the Agent Registry port."""

    @abstractmethod
    def list_all_agents(self) -> list[dict]:
        """List all registered models tagged as agents (model_type=agent).

        Each entry contains at least: name, creation_timestamp, aliases, tags,
        latest_versions.
        """
        pass

    @abstractmethod
    def list_agent_versions(self, agent_name: str) -> list[dict]:
        """List all versions of a registered agent."""
        pass

    @abstractmethod
    def get_agent_card(self, agent_name: str, agent_version: str) -> str | None:
        """Return the content of agent_card.md (or model_card.md) artifact, or None."""
        pass

    @abstractmethod
    def get_agent_governance_information(self, agent_name: str, agent_version: str) -> dict:
        """Return registered-model tags + run tags/params/metrics for an agent version.

        Returns
        -------
        dict with keys:
          - agent_name, agent_version, run_id
          - registered_model_tags: dict[str, str]
          - run_tags: dict[str, str]
        """
        pass
