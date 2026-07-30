"""MLflow Agent Registry Adapter.

Reads registered models that have the `model_type=agent` tag and exposes them
through the AgentRegistry port. Reuses MLflowClientManager so it shares the
connection pool with the ML model registry.
"""

import json
import os

import httpx
import mlflow
from loguru import logger
from mlflow.entities.model_registry import ModelVersion
from mlflow.store.entities import PagedList

from backend.domain.ports.agent_registry import AgentRegistry
from backend.infrastructure.mlflow_client import MLflowClientManager
from backend.utils import hash_directory


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

    def _logged_model_exists(self, model_id: str | None) -> bool:
        """MLflow 3.x: a ModelVersion's registry entry survives deleting its
        source LoggedModel (they're decoupled entities) — the version then
        points at nothing. Treat that as effectively deleted."""
        if not model_id:
            return True  # no LoggedModel to check against (e.g. legacy version) — assume alive
        try:
            self.mlflow_client.get_logged_model(model_id)
            return True
        except Exception:
            return False

    def _get_logged_model_experiment_id(self, model_id: str) -> str | None:
        """Best-effort lookup, isolated from _logged_model_exists so a failure here
        never affects whether the version is considered alive."""
        try:
            return self.mlflow_client.get_logged_model(model_id).experiment_id
        except Exception:
            return None

    @staticmethod
    def _extract_model_id_from_source(source: str | None) -> str | None:
        """ModelVersion.model_id is often unset even in MLflow 3.x (depends on how the
        version was registered); the LoggedModel id is still recoverable from the
        `models:/<model_id>` source URI when present."""
        if source and source.startswith("models:/"):
            return source[len("models:/") :]
        return None

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

    def download_agent_artifacts(self, agent_name: str, agent_version: str, destination_path: str) -> str:
        mlflow.set_tracking_uri(self.mlflow_client_manager.tracking_uri)
        agent_uri = f"models:/{agent_name}/{agent_version}"
        logger.info(f"Downloading agent artefacts for agent_uri: {agent_uri}")
        target_path = os.path.join(destination_path, "custom_agent")
        os.makedirs(target_path, exist_ok=True)
        mlflow.artifacts.download_artifacts(artifact_uri=agent_uri, dst_path=target_path)
        hash_value = hash_directory(target_path)
        hash_file_path = os.path.join(target_path, hash_value)
        with open(hash_file_path, "w") as f:
            f.write("")
        logger.info(f"Downloaded agent artefacts to: {target_path}")
        return target_path

    def get_deployment_config(self, agent_name: str, agent_version: str) -> dict[str, str]:
        try:
            run_id = self._get_run_id(agent_name, agent_version)
            if not run_id:
                return {}
            response = httpx.get(
                f"{self.mlflow_client_manager.tracking_uri}/get-artifact",
                params={"run_id": run_id, "path": "deployment_config.json"},
                timeout=2.0,
            )
            if response.status_code == 200:
                return json.loads(response.text)
            return {}
        except Exception as e:
            logger.warning(f"Could not fetch deployment_config for {agent_name} v{agent_version}: {e}")
            return {}

    def _get_run_id(self, agent_name: str, agent_version: str) -> str | None:
        for v in self.list_agent_versions(agent_name):
            if str(v["version"]) == str(agent_version):
                return v.get("run_id")
        return None

    def _process_versions(self, versions: list[ModelVersion]) -> list[dict]:
        processed = []
        for v in versions:
            model_id = getattr(v, "model_id", None)
            if not self._logged_model_exists(model_id):
                continue
            entry = {
                "name": v.name,
                "version": v.version,
                "creation_timestamp": v.creation_timestamp,
                "run_id": v.run_id,
            }
            registry_model_id = model_id or self._extract_model_id_from_source(getattr(v, "source", None))
            if registry_model_id:
                entry["model_id"] = registry_model_id
                entry["experiment_id"] = self._get_logged_model_experiment_id(registry_model_id)
            processed.append(entry)
        return processed
