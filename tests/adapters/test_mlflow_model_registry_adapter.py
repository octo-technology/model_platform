from unittest.mock import MagicMock

import pytest
from mlflow.entities.model_registry import RegisteredModel

from model_platform.adapters.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


@pytest.fixture
def mlflow_adapter():
    adapter = MLFlowModelRegistryAdapter()
    adapter.mlflow_client = MagicMock()
    return adapter


def test_list_all_models(mlflow_adapter):
    mock_models = [
        RegisteredModel(name="model1", creation_timestamp=1234567890),
        RegisteredModel(name="model2", creation_timestamp=1234567891),
    ]
    mlflow_adapter.mlflow_client.search_registered_models.return_value = mock_models

    result = mlflow_adapter.list_all_models()

    assert len(result) == 2
    assert result[0]["name"] == "model2"
    assert result[0]["creation_timestamp"] == 1234567891
    assert result[1]["name"] == "model1"
    assert result[1]["creation_timestamp"] == 1234567890


def test_process_mlflow_list():
    mock_models = [
        RegisteredModel(name="model1", creation_timestamp=1234567890),
        RegisteredModel(name="model2", creation_timestamp=1234567891),
    ]

    result = MLFlowModelRegistryAdapter._process_mlflow_list(mock_models)

    assert len(result) == 2
    assert result[0]["name"] == "model2"
    assert result[0]["creation_timestamp"] == 1234567891
    assert result[1]["name"] == "model1"
    assert result[1]["creation_timestamp"] == 1234567890
