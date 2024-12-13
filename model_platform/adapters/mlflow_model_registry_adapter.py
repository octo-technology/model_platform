"""MLFlow Model Registry Adapter module.

This module provides an adapter for interacting with the MLFlow Model Registry.
"""

from mlflow import MlflowClient
from mlflow.entities.model_registry import RegisteredModel

from model_platform.domain.ports.model_registry import ModelRegistry


class MLFlowModelRegistryAdapter(ModelRegistry):
    """Adapter for interacting with the MLFlow Model Registry."""

    def __init__(self):
        """Initialize the MLFlowModelRegistryAdapter instance."""
        super().__init__()
        self.mlflow_client: MlflowClient = MlflowClient()

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
            {"name": model.name, "creation_timestamp": model.creation_timestamp}
            for model in mlflow_registered_model_list
        ]
        processed_list.sort(key=lambda x: x["creation_timestamp"], reverse=True)
        return processed_list


if __name__ == "__main__":
    mlflow_adapter = MLFlowModelRegistryAdapter()
    for model in mlflow_adapter.list_all_models():
        print(model.name, model.creation_timestamp)
