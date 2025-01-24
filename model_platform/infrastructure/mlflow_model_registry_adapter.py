"""MLFlow Model Registry Adapter module.

This module provides an adapter for interacting with the MLFlow Model Registry.
"""

import os

from loguru import logger
from mlflow import MlflowClient
from mlflow.entities import FileInfo
from mlflow.entities.model_registry import ModelVersion, RegisteredModel

from model_platform.domain.ports.model_registry import ModelRegistry


class MLFlowModelRegistryAdapter(ModelRegistry):
    """Adapter for interacting with the MLFlow Model Registry."""

    def __init__(self, mlflow_client: MlflowClient):
        """Initialize the MLFlowModelRegistryAdapter instance."""
        super().__init__()
        self.mlflow_client: MlflowClient = mlflow_client

    def list_all_models(self) -> list[dict[str, str | int]]:
        """List all registered models in the MLFlow Model Registry by querying the MLFlow client.

        Returns
        -------
            list[dict[str, str | int]]: A list of dictionaries containing model attributes.
        """
        registered_model_list = self.mlflow_client.search_registered_models()
        return self._process_mlflow_list(registered_model_list)

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
        file_info: FileInfo = self.mlflow_client.list_artifacts(run_id)[0]
        return file_info.path

    def _download_run_id_artifacts(self, run_id: str, artifacts_path: str, destination_path: str) -> str:
        return self.mlflow_client.download_artifacts(run_id, artifacts_path, destination_path)

    def download_model_artifacts(self, model_name: str, version: str, destination_path: str) -> str:
        run_id = self._get_model_run_id(model_name, version)
        logger.info(f"Downloading model artefacts for run_id: {run_id}")
        artifacts_path: str = self._get_model_artifacts_path(run_id)
        downloaded_artifacts_path = self._download_run_id_artifacts(run_id, artifacts_path, destination_path)
        downloaded_artifacts_path = os.path.join(destination_path, downloaded_artifacts_path)
        logger.info(f"Downloaded model artefacts to: {downloaded_artifacts_path}")
        return downloaded_artifacts_path

    def _get_model_run_id(self, model_name: str, version: str) -> str:
        registered_model: RegisteredModel = self.mlflow_client.get_registered_model(model_name)
        run_id = [
            model_version for model_version in registered_model.latest_versions if model_version.version == version
        ][0].run_id

        return run_id
