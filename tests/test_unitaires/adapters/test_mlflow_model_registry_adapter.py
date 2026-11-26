from types import SimpleNamespace
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
    mock_client_manager.tracking_uri = "http://mlflow.test:5000"

    mock_client.get_model_version.return_value = ModelVersion(
        name="model1", version="1", creation_timestamp=1000, run_id="run_123"
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "# My Model Card"

    patch_target = "backend.infrastructure.mlflow_model_registry_adapter.httpx.get"
    with patch(patch_target, return_value=mock_response) as mock_get:
        adapter = MLFlowModelRegistryAdapter(mock_client_manager)
        content = adapter.get_model_card("model1", "1")

    assert content == "# My Model Card"
    mock_get.assert_called_once_with(
        "http://mlflow.test:5000/get-artifact",
        params={"run_id": "run_123", "path": "model_card.md"},
    )


def test_get_model_card_returns_none_when_absent(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager
    mock_client_manager.tracking_uri = "http://mlflow.test:5000"

    mock_client.get_model_version.return_value = ModelVersion(
        name="model1", version="1", creation_timestamp=1000, run_id="run_123"
    )

    mock_response = MagicMock()
    mock_response.status_code = 404

    patch_target = "backend.infrastructure.mlflow_model_registry_adapter.httpx.get"
    with patch(patch_target, return_value=mock_response):
        adapter = MLFlowModelRegistryAdapter(mock_client_manager)
        content = adapter.get_model_card("model1", "1")

    assert content is None


def test_get_model_card_returns_none_on_error(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_client.get_model_version.side_effect = Exception("MLflow unreachable")

    adapter = MLFlowModelRegistryAdapter(mock_client_manager)
    content = adapter.get_model_card("model1", "1")

    assert content is None


def test_get_logged_model_returns_loggedmodel_data(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_client.get_model_version.return_value = SimpleNamespace(
        name="model1", version="1", creation_timestamp=2000, run_id="run_123", model_id="m-abc"
    )

    fake_logged_model = SimpleNamespace(
        creation_timestamp=1500,
        source_run_id="run_123",
        tags={"env": "staging"},
        params={"lr": "0.01"},
        metrics=[SimpleNamespace(key="accuracy", value=0.95)],
    )
    mock_client.get_logged_model.return_value = fake_logged_model

    fake_model_info = SimpleNamespace(
        flavors={"sklearn": {}, "python_function": {}},
        signature=SimpleNamespace(to_dict=lambda: {"inputs": "[c1]", "outputs": "[c2]"}),
    )

    with patch(
        "backend.infrastructure.mlflow_model_registry_adapter.mlflow.models.get_model_info",
        return_value=fake_model_info,
    ):
        adapter = MLFlowModelRegistryAdapter(mock_client_manager)
        logged = adapter.get_logged_model("model1", "1")

    assert logged["model_id"] == "m-abc"
    assert logged["tags"] == {"env": "staging"}
    assert logged["params"] == {"lr": "0.01"}
    assert logged["metrics"] == {"accuracy": 0.95}
    assert set(logged["flavors"]) == {"sklearn", "python_function"}
    assert logged["signature"] == {"inputs": "[c1]", "outputs": "[c2]"}
    assert logged["model_uri"] == "models:/model1/1"


def test_get_model_governance_information_merges_logged_model_and_run(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager

    mock_client.get_model_version.return_value = SimpleNamespace(
        name="model1", version="1", creation_timestamp=2000, run_id="run_123", model_id="m-abc"
    )
    mock_client.get_logged_model.return_value = SimpleNamespace(
        creation_timestamp=1500,
        source_run_id="run_123",
        tags={"env": "staging"},
        params={"lr": "0.01"},
        metrics=[SimpleNamespace(key="accuracy", value=0.95)],
    )
    mock_client.get_run.return_value = SimpleNamespace(
        data=SimpleNamespace(
            tags={"mlflow.user": "alice", "mlflow.runName": "r1"},
            params={"seed": "42"},
            metrics={"f1": 0.9},
        )
    )

    fake_model_info = SimpleNamespace(
        flavors={"sklearn": {}, "python_function": {}},
        signature=SimpleNamespace(to_dict=lambda: {"inputs": "[c1]", "outputs": "[c2]"}),
    )

    with patch(
        "backend.infrastructure.mlflow_model_registry_adapter.mlflow.models.get_model_info",
        return_value=fake_model_info,
    ):
        adapter = MLFlowModelRegistryAdapter(mock_client_manager)
        gov = adapter.get_model_governance_information("model1", "1")

    assert gov["model_id"] == "m-abc"
    assert gov["run_id"] == "run_123"
    assert gov["tags"]["mlflow.user"] == "alice"
    assert gov["tags"]["env"] == "staging"
    assert gov["params"] == {"seed": "42", "lr": "0.01"}
    assert gov["metrics"] == {"f1": 0.9, "accuracy": 0.95}
    assert gov["signature"] == {"inputs": "[c1]", "outputs": "[c2]"}


def test_log_model_translates_artifact_path_to_name(mock_mlflow_client_manager):
    mock_client_manager, mock_client = mock_mlflow_client_manager
    mock_client.tracking_uri = "http://mlflow.test:5000"

    with (
        patch("mlflow.pyfunc.log_model") as mock_log,
        patch("mlflow.set_tracking_uri"),
    ):
        adapter = MLFlowModelRegistryAdapter(mock_client_manager)
        adapter.log_model(artifact_path="custom_model", python_model=object())

    kwargs = mock_log.call_args.kwargs
    assert "artifact_path" not in kwargs
    assert kwargs["name"] == "custom_model"
