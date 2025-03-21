"""MLFlow Model Registry Adapter module.

This module provides an adapter for interacting with the MLFlow Model Registry.
"""

import os

import mlflow
from loguru import logger
from mlflow import MlflowClient
from mlflow.entities import FileInfo
from mlflow.entities.model_registry import ModelVersion, RegisteredModel
from mlflow.store.entities import PagedList

from model_platform.domain.ports.model_registry import ModelRegistry
from model_platform.infrastructure.mlflow_client import MLflowClientManager
from model_platform.utils import hash_directory


class MLFlowModelRegistryAdapter(ModelRegistry):
    """Adapter for interacting with the MLFlow Model Registry."""

    def __init__(self, mlflow_client_manager: MLflowClientManager):
        """Initialize the MLFlowModelRegistryAdapter instance."""
        super().__init__()
        self.mlflow_client_manager: MLflowClientManager = mlflow_client_manager

    @property
    def mlflow_client(self) -> MlflowClient:
        return self.mlflow_client_manager.client

        # TODO problème avec la tracking uri pour un list artifacts

    def list_all_models(self) -> list[dict[str, str | int]]:
        """List all registered models in the MLFlow Model Registry by querying the MLFlow client.

        Returns
        -------
            list[dict[str, str | int]]: A list of dictionaries containing model attributes.
        """
        registered_model_list = self.mlflow_client.search_registered_models()
        logger.info(f"Got following models: {registered_model_list}")
        return self._process_mlflow_list(registered_model_list)

    def list_model_versions(self, model_name: str) -> list[dict]:
        """List all versions of a registered model in the MLFlow Model Registry by querying the MLFlow client.

        Parameters
        ----------
        model_name : str
            The name of the model to list versions for.

        Returns
        -------
        list[dict[str, str | int]]
            A list of dictionaries containing model version attributes.
        """
        all_model_versions: PagedList[ModelVersion] = self.mlflow_client.search_model_versions(f"name='{model_name}'")
        all_model_versions_processed: list[dict] = self._process_model_versions(all_model_versions.to_list())
        return all_model_versions_processed

    @staticmethod
    def _process_mlflow_list(mlflow_registered_model_list: list[RegisteredModel]) -> list[dict[str, str | int]]:
        """Process a list of MLFlow registered models and return a sorted list of dictionaries.

        Parameters
        ----------
        mlflow_registered_model_list : list[RegisteredModel]
            A list of MLFlow registered models to be processed.

        Returns
        -------
        list[dict[str, str | int]]
        A list of dictionaries containing model attributes, sorted by creation timestamp in descending order.
        """
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
        processed_versions = [
            {
                "name": version.name,
                "version": version.version,
                "creation_timestamp": version.creation_timestamp,
                "run_id": version.run_id,
            }
            for version in model_version
        ]

        return processed_versions

    def _get_model_artifacts_path(self, run_id: str) -> str:
        logger.info(f"Using mlflow tracking uri: {self.mlflow_client_manager.tracking_uri}")
        logger.info(f"Using mlflow tracking uri: {self.mlflow_client.tracking_uri}")
        file_info: FileInfo = self.mlflow_client.list_artifacts(run_id)[0]
        return file_info.path

    def _download_run_id_artifacts(self, run_id: str, artifacts_path: str, destination_path: str) -> str:
        return self.mlflow_client.download_artifacts(run_id, artifacts_path, destination_path)

    def download_model_artifacts(self, model_name: str, version: str, destination_path: str) -> str:
        mlflow.set_tracking_uri(self.mlflow_client_manager.tracking_uri)
        run_id = self._get_model_run_id(model_name, version)
        logger.info(f"Downloading model artefacts for run_id: {run_id}")
        artifacts_path: str = self._get_model_artifacts_path(run_id)
        downloaded_artifacts_path = self._download_run_id_artifacts(run_id, artifacts_path, destination_path)
        downloaded_artifacts_path = os.path.join(destination_path, downloaded_artifacts_path)
        hash_value = hash_directory(downloaded_artifacts_path)
        hash_file_path = os.path.join(downloaded_artifacts_path, hash_value)
        with open(hash_file_path, "w") as f:
            f.write("")
        logger.info(f"Downloaded model artefacts to: {downloaded_artifacts_path}")
        return downloaded_artifacts_path

    def _get_model_run_id(self, model_name: str, version: str) -> str:
        model_versions: list[dict] = self.list_model_versions(model_name)
        run_id = [model_version["run_id"] for model_version in model_versions if model_version["version"] == version][0]

        return run_id

    def get_model_governance_information(self, model_name: str, version: str) -> dict:
        run_id = self._get_model_run_id(model_name, version)
        model_tags = self.mlflow_client.get_run(run_id).data.tags
        model_params = self.mlflow_client.get_run(run_id).data.params
        model_metrics = self.mlflow_client.get_run(run_id).data.metrics
        return {
            "model_name": model_name,
            "version": version,
            "run_id": run_id,
            "tags": model_tags,
            "params": model_params,
            "metrics": model_metrics,
        }


if __name__ == "__main__":
    mlflow_client_manager = MLflowClientManager(tracking_uri="http://model-platform.com/registry/test/")
    mlflow_client_manager.initialize()
    registry_adapter = MLFlowModelRegistryAdapter(mlflow_client_manager=mlflow_client_manager)
    print(registry_adapter.get_model_governance_information("test_model", "4"))
