from unittest.mock import MagicMock, patch

from backend.infrastructure.mlflow_agent_registry_adapter import MLFlowAgentRegistryAdapter


def _adapter_with_run_id(run_id="run-123"):
    client_manager = MagicMock()
    client_manager.tracking_uri = "http://mlflow.example.com"
    adapter = MLFlowAgentRegistryAdapter(client_manager)
    adapter._get_run_id = MagicMock(return_value=run_id)
    return adapter


class TestGetDeploymentConfig:
    def test_returns_parsed_json_artifact(self):
        adapter = _adapter_with_run_id()
        response = MagicMock(status_code=200, text='{"PG_HOST": "host.minikube.internal", "PG_DB": "ecommerce"}')

        with patch("backend.infrastructure.mlflow_agent_registry_adapter.httpx.get", return_value=response) as get:
            config = adapter.get_deployment_config("my_agent", "1")

        assert config == {"PG_HOST": "host.minikube.internal", "PG_DB": "ecommerce"}
        get.assert_called_once_with(
            "http://mlflow.example.com/get-artifact",
            params={"run_id": "run-123", "path": "deployment_config.json"},
            timeout=2.0,
        )

    def test_returns_empty_dict_when_artifact_missing(self):
        adapter = _adapter_with_run_id()
        response = MagicMock(status_code=404)

        with patch("backend.infrastructure.mlflow_agent_registry_adapter.httpx.get", return_value=response):
            assert adapter.get_deployment_config("my_agent", "1") == {}

    def test_returns_empty_dict_when_no_run_id(self):
        adapter = _adapter_with_run_id(run_id=None)

        assert adapter.get_deployment_config("my_agent", "1") == {}

    def test_returns_empty_dict_on_exception(self):
        adapter = _adapter_with_run_id()

        with patch("backend.infrastructure.mlflow_agent_registry_adapter.httpx.get", side_effect=Exception("boom")):
            assert adapter.get_deployment_config("my_agent", "1") == {}
