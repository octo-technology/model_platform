"""MLFlow Model Registry Adapter (MLflow 3.x with LoggedModel).

This module provides an adapter for interacting with the MLFlow Model Registry.
In MLflow 3.x, models are first-class entities (LoggedModel) decoupled from runs.
Governance info (metrics, params, tags, signature, flavors) is sourced directly
from the LoggedModel rather than parsed from run-level `mlflow.log-model.history` tags.
"""

import os

import httpx
import mlflow
from loguru import logger
from mlflow import MlflowClient
from mlflow.entities import FileInfo
from mlflow.entities.model_registry import ModelVersion, RegisteredModel
from mlflow.store.entities import PagedList

from backend.domain.ports.model_registry import ModelRegistry
from backend.infrastructure.mlflow_client import MLflowClientManager
from backend.utils import hash_directory


class MLFlowModelRegistryAdapter(ModelRegistry):
    """Adapter for the MLflow Model Registry (3.x)."""

    def __init__(self, mlflow_client_manager: MLflowClientManager):
        super().__init__()
        self.mlflow_client_manager: MLflowClientManager = mlflow_client_manager

    @property
    def mlflow_client(self) -> MlflowClient:
        return self.mlflow_client_manager.client

    # -------------------------------------------------------------------------
    # Registered models (used for promotion + listing)
    # -------------------------------------------------------------------------

    def list_all_models(self) -> list[dict[str, str | int]]:
        registered_model_list = self.mlflow_client.search_registered_models()
        logger.debug(f"Got following models: {registered_model_list}")
        return self._process_mlflow_list(registered_model_list)

    def list_model_versions(self, model_name: str) -> list[dict]:
        all_model_versions: PagedList[ModelVersion] = self.mlflow_client.search_model_versions(f"name='{model_name}'")
        return self._process_model_versions(all_model_versions.to_list())

    @staticmethod
    def _process_mlflow_list(mlflow_registered_model_list: list[RegisteredModel]) -> list[dict[str, str | int]]:
        processed_list = [
            {
                "name": model.name,
                "creation_timestamp": model.creation_timestamp,
                "aliases": model.aliases,
                "latest_versions": MLFlowModelRegistryAdapter._process_model_versions(model.latest_versions),
            }
            for model in mlflow_registered_model_list
        ]
        processed_list.sort(key=lambda x: x["creation_timestamp"], reverse=True)
        return processed_list

    @staticmethod
    def _process_model_versions(model_version: list[ModelVersion]) -> list[dict]:
        processed_versions = []
        for version in model_version:
            entry = {
                "name": version.name,
                "version": version.version,
                "creation_timestamp": version.creation_timestamp,
                "run_id": version.run_id,
            }
            # MLflow 3.x: ModelVersion has model_id pointing to a LoggedModel
            model_id = getattr(version, "model_id", None)
            if model_id:
                entry["model_id"] = model_id
            processed_versions.append(entry)
        return processed_versions

    # -------------------------------------------------------------------------
    # Artifacts
    # -------------------------------------------------------------------------

    def _get_model_artifacts_path(self, run_id: str) -> str:
        logger.info(f"Using mlflow tracking uri: {self.mlflow_client_manager.tracking_uri}")
        artifacts: list[FileInfo] = self.mlflow_client.list_artifacts(run_id)
        model_artifact = next((a for a in artifacts if a.is_dir), artifacts[0])
        return model_artifact.path

    def _download_run_id_artifacts(self, run_id: str, artifacts_path: str, destination_path: str) -> str:
        return self.mlflow_client.download_artifacts(run_id, artifacts_path, destination_path)

    def download_model_artifacts(self, model_name: str, version: str, destination_path: str) -> str:
        mlflow.set_tracking_uri(self.mlflow_client_manager.tracking_uri)
        model_uri = f"models:/{model_name}/{version}"
        logger.info(f"Downloading model artefacts for model_uri: {model_uri}")
        target_path = os.path.join(destination_path, "custom_model")
        os.makedirs(target_path, exist_ok=True)
        mlflow.artifacts.download_artifacts(artifact_uri=model_uri, dst_path=target_path)
        hash_value = hash_directory(target_path)
        hash_file_path = os.path.join(target_path, hash_value)
        with open(hash_file_path, "w") as f:
            f.write("")
        logger.info(f"Downloaded model artefacts to: {target_path}")
        return target_path

    def _get_model_version_entity(self, model_name: str, version: str) -> ModelVersion:
        return self.mlflow_client.get_model_version(model_name, version)

    def _get_model_run_id(self, model_name: str, version: str) -> str:
        return self._get_model_version_entity(model_name, version).run_id

    def get_model_card(self, model_name: str, version: str) -> str | None:
        try:
            run_id = self._get_model_run_id(model_name, version)
            response = httpx.get(
                f"{self.mlflow_client_manager.tracking_uri}/get-artifact",
                params={"run_id": run_id, "path": "model_card.md"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Could not fetch model_card.md for {model_name} v{version}: {e}")
            return None

    # -------------------------------------------------------------------------
    # LoggedModel (MLflow 3.x first-class entity)
    # -------------------------------------------------------------------------

    def get_logged_model(self, model_name: str, version: str) -> dict:
        mv = self._get_model_version_entity(model_name, version)
        model_id = getattr(mv, "model_id", None)
        model_uri = f"models:/{model_name}/{version}"

        logged_model_data = self._fetch_logged_model(model_id) if model_id else None
        model_info_data = self._fetch_model_info(model_uri)

        return {
            "model_id": model_id,
            "name": model_name,
            "version": version,
            "creation_timestamp": (
                logged_model_data.get("creation_timestamp") if logged_model_data else mv.creation_timestamp
            ),
            "source_run_id": logged_model_data.get("source_run_id") if logged_model_data else mv.run_id,
            "tags": (logged_model_data or {}).get("tags", {}),
            "params": (logged_model_data or {}).get("params", {}),
            "metrics": (logged_model_data or {}).get("metrics", {}),
            "flavors": model_info_data.get("flavors", []),
            "signature": model_info_data.get("signature"),
            "model_uri": model_uri,
        }

    def _fetch_logged_model(self, model_id: str) -> dict | None:
        """Fetch LoggedModel via MLflow 3.x client API."""
        try:
            logged_model = self.mlflow_client.get_logged_model(model_id)
            return {
                "creation_timestamp": getattr(logged_model, "creation_timestamp", None),
                "source_run_id": getattr(logged_model, "source_run_id", None),
                "tags": dict(getattr(logged_model, "tags", {}) or {}),
                "params": dict(getattr(logged_model, "params", {}) or {}),
                "metrics": self._extract_metrics(logged_model),
            }
        except Exception as e:
            logger.warning(f"Could not fetch LoggedModel {model_id}: {e}")
            return None

    @staticmethod
    def _extract_metrics(logged_model) -> dict:
        """LoggedModel.metrics is a list of Metric entities in 3.x; flatten to {key: value}."""
        raw = getattr(logged_model, "metrics", None) or []
        if isinstance(raw, dict):
            return raw
        result: dict = {}
        for m in raw:
            key = getattr(m, "key", None) or (m.get("key") if isinstance(m, dict) else None)
            value = getattr(m, "value", None) or (m.get("value") if isinstance(m, dict) else None)
            if key is not None:
                result[key] = value
        return result

    def _fetch_model_info(self, model_uri: str) -> dict:
        """Fetch flavors and signature via mlflow.models.get_model_info (reads MLmodel file)."""
        try:
            mlflow.set_tracking_uri(self.mlflow_client_manager.tracking_uri)
            info = mlflow.models.get_model_info(model_uri)
            flavors = list(info.flavors.keys()) if getattr(info, "flavors", None) else []
            signature = None
            if getattr(info, "signature", None) is not None:
                signature_obj = info.signature
                signature = signature_obj.to_dict() if hasattr(signature_obj, "to_dict") else dict(signature_obj)
            return {"flavors": flavors, "signature": signature}
        except Exception as e:
            logger.warning(f"Could not fetch model info for {model_uri}: {e}")
            return {"flavors": [], "signature": None}

    # -------------------------------------------------------------------------
    # Governance (LoggedModel + source run)
    # -------------------------------------------------------------------------

    def get_model_governance_information(self, model_name: str, version: str) -> dict:
        logged = self.get_logged_model(model_name, version)
        run_id = logged["source_run_id"]

        run_tags: dict = {}
        run_params: dict = {}
        run_metrics: dict = {}
        if run_id:
            try:
                run = self.mlflow_client.get_run(run_id)
                run_tags = dict(run.data.tags or {})
                run_params = dict(run.data.params or {})
                run_metrics = dict(run.data.metrics or {})
            except Exception as e:
                logger.warning(f"Could not fetch source run {run_id}: {e}")

        # Merged tags: run tags first, model tags override (model is authoritative)
        merged_tags = {**run_tags, **logged["tags"]}
        # Params/metrics: prefer model-level (LoggedModel), fall back to run-level
        merged_params = {**run_params, **logged["params"]}
        merged_metrics = {**run_metrics, **logged["metrics"]}

        return {
            "model_name": model_name,
            "version": version,
            "model_id": logged["model_id"],
            "run_id": run_id,
            "creation_timestamp": logged["creation_timestamp"],
            "tags": merged_tags,
            "params": merged_params,
            "metrics": merged_metrics,
            "flavors": logged["flavors"],
            "signature": logged["signature"],
            "model_uri": logged["model_uri"],
        }

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    def sync_run_data_to_model_version_tags(self, model_name: str, version: str) -> None:
        """Copy run tags to model version tags and run description to model version description."""
        try:
            governance = self.get_model_governance_information(model_name, version)
        except Exception as e:
            logger.warning(f"Could not get governance info for {model_name} v{version}: {e}")
            return

        tags = governance.get("tags", {})

        for key, value in tags.items():
            if not key.startswith("mlflow."):
                try:
                    self.mlflow_client.set_model_version_tag(model_name, version, key, str(value)[:500])
                except Exception as e:
                    logger.warning(f"Could not set tag '{key}' on {model_name} v{version}: {e}")

        description = tags.get("mlflow.note.content")
        if description:
            try:
                self.mlflow_client.update_model_version(model_name, version, description=description[:5000])
            except Exception as e:
                logger.warning(f"Could not set description on {model_name} v{version}: {e}")

    def sync_run_data_to_registered_model_tags(self, model_name: str, version: str) -> None:
        """Copy run tags and description of a version to the registered model level."""
        try:
            governance = self.get_model_governance_information(model_name, version)
        except Exception as e:
            logger.warning(f"Could not get governance info for {model_name} v{version}: {e}")
            return

        tags = governance.get("tags", {})

        for key, value in tags.items():
            if not key.startswith("mlflow."):
                try:
                    self.mlflow_client.set_registered_model_tag(model_name, key, str(value)[:500])
                except Exception as e:
                    logger.warning(f"Could not set registered model tag '{key}' on {model_name}: {e}")

        description = tags.get("mlflow.note.content")
        if description:
            try:
                self.mlflow_client.update_registered_model(model_name, description=description[:5000])
            except Exception as e:
                logger.warning(f"Could not set description on registered model {model_name}: {e}")

    def log_model(self, **kwargs) -> None:
        """Log a pyfunc model. MLflow 3.x uses `name=` (legacy `artifact_path=` is translated)."""
        if "artifact_path" in kwargs and "name" not in kwargs:
            kwargs["name"] = kwargs.pop("artifact_path")
        client = self.mlflow_client
        logger.info(client.tracking_uri)
        mlflow.set_tracking_uri(client.tracking_uri)
        mlflow.pyfunc.log_model(**kwargs)


if __name__ == "__main__":
    mlflow_client_manager = MLflowClientManager(tracking_uri="http://model-platform.com/registry/test/")
    mlflow_client_manager.initialize()
    registry_adapter = MLFlowModelRegistryAdapter(mlflow_client_manager=mlflow_client_manager)
    print(registry_adapter.get_model_governance_information("test_model", "4"))
