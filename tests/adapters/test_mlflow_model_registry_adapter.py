from unittest.mock import MagicMock

import pytest
from mlflow.entities.model_registry import RegisteredModel, ModelVersion

from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


@pytest.fixture
def mlflow_adapter():
    mlflow_client = MagicMock()
    adapter = MLFlowModelRegistryAdapter(mlflow_client)
    return adapter


@pytest.fixture()
def mock_models():
    model_1_latest_version = [
        ModelVersion(name="model1", version="1", creation_timestamp=1234567890, description="bla", run_id="A1234567890")
    ]
    model_2_latest_version = [
        ModelVersion(
            name="model2", version="1", creation_timestamp=1234567890, description="bla", run_id="B1234567890"
        ),
        ModelVersion(
            name="model2", version="2", creation_timestamp=1234567891, description="bla", run_id="C1234567891"
        ),
    ]
    mock_models = [
        RegisteredModel(name="model1", creation_timestamp=1234567890, latest_versions=model_1_latest_version),
        RegisteredModel(name="model2", creation_timestamp=1234567891, latest_versions=model_2_latest_version),
    ]
    return mock_models


def test_list_all_models(mlflow_adapter, mock_models):
    mlflow_adapter.mlflow_client.search_registered_models.return_value = mock_models

    result = mlflow_adapter.list_all_models()

    assert len(result) == 2
    assert result[0]["name"] == "model2"
    assert result[0]["creation_timestamp"] == 1234567891
    assert result[1]["name"] == "model1"
    assert result[1]["creation_timestamp"] == 1234567890


def test_process_mlflow_list(mock_models):
    result = MLFlowModelRegistryAdapter._process_mlflow_list(mock_models)

    assert len(result) == 2
    assert result[0]["name"] == "model2"
    assert result[0]["creation_timestamp"] == 1234567891
    assert result[1]["name"] == "model1"
    assert result[1]["creation_timestamp"] == 1234567890


def test_get_model_run_id(mlflow_adapter, mock_models):
    mlflow_adapter.mlflow_client.get_registered_model.return_value = mock_models[0]

    run_id = mlflow_adapter._get_model_run_id("model1", "1")

    assert "A1234567890" == run_id
