"""MLflow Agent Registry Adapter.

Reads registered models that have the `model_type=agent` tag and exposes them
through the AgentRegistry port. Reuses MLflowClientManager so it shares the
connection pool with the ML model registry.
"""

import httpx
from loguru import logger
from mlflow.entities.model_registry import ModelVersion
from mlflow.store.entities import PagedList

from backend.domain.ports.agent_registry import AgentRegistry
from backend.infrastructure.mlflow_client import MLflowClientManager


class MLFlowAgentRegistryAdapter(AgentRegistry):
    def __init__(self, mlflow_client_manager: MLflowClientManager):
        self.mlflow_client_manager: MLflowClientManager = mlflow_client_manager

    @property
    def mlflow_client(self):
        return self.mlflow_client_manager.client

    def list_all_agents(self) -> list[dict]:
        # Filter in Python (MLflow tag filters are restrictive)
        agents = [m for m in self.mlflow_client.search_registered_models() if m.tags.get("model_type") == "agent"]
        return [
            {
                "name": a.name,
                "creation_timestamp": a.creation_timestamp,
                "aliases": a.aliases,
                "tags": dict(a.tags or {}),
                "latest_versions": self._process_versions(a.latest_versions),
            }
            for a in agents
        ]

    def list_agent_versions(self, agent_name: str) -> list[dict]:
        versions: PagedList[ModelVersion] = self.mlflow_client.search_model_versions(f"name='{agent_name}'")
        return self._process_versions(versions.to_list())

    def get_agent_card(self, agent_name: str, agent_version: str) -> str | None:
        try:
            run_id = self._get_run_id(agent_name, agent_version)
            if not run_id:
                return None
            # Try both naming conventions
            for path in ("agent_card.md", "model_card.md"):
                response = httpx.get(
                    f"{self.mlflow_client_manager.tracking_uri}/get-artifact",
                    params={"run_id": run_id, "path": path},
                    timeout=2.0,
                )
                if response.status_code == 200:
                    return response.text
            return None
        except Exception as e:
            logger.warning(f"Could not fetch agent_card for {agent_name} v{agent_version}: {e}")
            return None

    def get_agent_governance_information(self, agent_name: str, agent_version: str) -> dict:
        run_id = self._get_run_id(agent_name, agent_version)
        registered_model = self.mlflow_client.get_registered_model(agent_name)
        run_tags: dict[str, str] = {}
        if run_id:
            try:
                run_tags = dict(self.mlflow_client.get_run(run_id).data.tags or {})
            except Exception:
                pass
        return {
            "agent_name": agent_name,
            "agent_version": agent_version,
            "run_id": run_id,
            "registered_model_tags": dict(registered_model.tags or {}),
            "run_tags": run_tags,
        }

    def _get_run_id(self, agent_name: str, agent_version: str) -> str | None:
        for v in self.list_agent_versions(agent_name):
            if str(v["version"]) == str(agent_version):
                return v.get("run_id")
        return None

    @staticmethod
    def _process_versions(versions: list[ModelVersion]) -> list[dict]:
        return [
            {
                "name": v.name,
                "version": v.version,
                "creation_timestamp": v.creation_timestamp,
                "run_id": v.run_id,
            }
            for v in versions
        ]
