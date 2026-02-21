import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from mlflow.entities import FileInfo
from mlflow.entities.model_registry import ModelVersion, RegisteredModel
from mlflow.store.entities import PagedList

from backend.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


@pytest.fixture
def mock_mlflow_client_manager():
    with patch("backend.infrastructure.mlflow_client.MLflowClientManager") as MockClientManager:
        mock_client_manager = MockClientManager.return_value
        mock_client = MagicMock()
        mock_client_manager.client = mock_client
        yield mock_client_manager, mock_client


def test_list_all_models(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_registered_models = [
        RegisteredModel(name="model1", creation_timestamp=1000, aliases={}, latest_versions=[]),
        RegisteredModel(name="model2", creation_timestamp=2000, aliases={}, latest_versions=[]),
    ]
    mock_client.search_registered_models.return_value = mock_registered_models

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    models = adapter.list_all_models()

    assert len(models) == 2
    assert models[0]["name"] == "model2"
    assert models[1]["name"] == "model1"


def test_list_model_versions(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_model_versions = [
        ModelVersion(name="model1", version="1", creation_timestamp=1000, run_id="run_123"),
        ModelVersion(name="model1", version="2", creation_timestamp=2000, run_id="run_456"),
    ]
    mock_client.search_model_versions.return_value = PagedList(mock_model_versions, token=None)

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    versions = adapter.list_model_versions("model1")

    assert len(versions) == 2
    assert versions[0]["version"] == "1"
    assert versions[1]["version"] == "2"


def test_get_model_artifacts_path(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_file_info = [FileInfo(path="artifacts/path", is_dir=False, file_size=123)]
    mock_client.list_artifacts.return_value = mock_file_info

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    artifacts_path = adapter._get_model_artifacts_path("run_123")

    assert artifacts_path == "artifacts/path"


def test_download_run_id_artifacts(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_client.download_artifacts.return_value = "downloaded/path"

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    downloaded_path = adapter._download_run_id_artifacts("run_123", "artifacts/path", "/destination")

    assert downloaded_path == "downloaded/path"


def test_get_model_card_returns_content_when_present(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_client.search_model_versions.return_value = PagedList(
        [ModelVersion(name="model1", version="1", creation_timestamp=1000, run_id="run_123")], token=None
    )
    mock_client.list_artifacts.return_value = [FileInfo(path="model_card.md", is_dir=False, file_size=42)]

    with tempfile.TemporaryDirectory() as tmp_dir:
        card_path = os.path.join(tmp_dir, "model_card.md")
        with open(card_path, "w") as f:
            f.write("# My Model Card")
        mock_client.download_artifacts.return_value = card_path

        adapter = MLFlowModelRegistryAdapter(mock_client_manager)
        content = adapter.get_model_card("model1", "1")

    assert content == "# My Model Card"


def test_get_model_card_returns_none_when_absent(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_client.search_model_versions.return_value = PagedList(
        [ModelVersion(name="model1", version="1", creation_timestamp=1000, run_id="run_123")], token=None
    )
    mock_client.list_artifacts.return_value = [FileInfo(path="model.pkl", is_dir=False, file_size=100)]

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    content = adapter.get_model_card("model1", "1")

    assert content is None
    mock_client.download_artifacts.assert_not_called()


def test_get_model_card_returns_none_on_error(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_client.search_model_versions.side_effect = Exception("MLflow unreachable")

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    content = adapter.get_model_card("model1", "1")

    assert content is None


def test_get_model_run_id(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_model_versions = [
        {"name": "model1", "version": "1", "run_id": "run_123", "creation_timestamp": 1000},
        {"name": "model1", "version": "2", "run_id": "run_456", "creation_timestamp": 2000},
    ]
    mock_client.search_model_versions.return_value = PagedList(
        [ModelVersion(**mv) for mv in mock_model_versions], token=None
    )

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    run_id = adapter._get_model_run_id("model1", "1")

    assert run_id == "run_123"
