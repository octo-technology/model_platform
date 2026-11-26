import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("MP_HOST_NAME", "localhost")
os.environ.setdefault("MP_DEPLOYMENT_PATH", "/deploy")
os.environ.setdefault("MP_DEPLOYMENT_PORT", "8000")


@pytest.fixture
def adapter():
    with patch("backend.infrastructure.k8s_deployment.config.load_kube_config", return_value=None):
        from backend.infrastructure.k8s_agent_deployment_adapter import K8SAgentDeployment

        deployment = K8SAgentDeployment(
            project_name="Credit-Risk-Assessment",
            model_name="ecommerce_text2sql",
            model_version="1",
            dashboard_uid="dash-123",
            env_vars={"PG_HOST": "host.minikube.internal", "PG_DB": "ecommerce", "MAMMOUTH_AGENT_MODEL": "gpt-4.1"},
        )
        deployment.apps_api_instance = MagicMock()
        yield deployment


def _deployed_body(adapter):
    """Return the V1Deployment body passed to create/replace_namespaced_deployment."""
    if adapter.apps_api_instance.create_namespaced_deployment.called:
        return adapter.apps_api_instance.create_namespaced_deployment.call_args.kwargs["body"]
    return adapter.apps_api_instance.replace_namespaced_deployment.call_args.kwargs["body"]


class TestK8SAgentDeploymentEnv:
    def test_no_hardcoded_secrets_in_generated_env(self, adapter):
        adapter._create_model_service_deployment()

        container = _deployed_body(adapter).spec.template.spec.containers[0]
        env_names = {e.name for e in container.env}
        assert "MAMMOUTH_API_KEY" not in env_names
        assert "PG_PASSWORD" not in env_names

    def test_agent_info_env_vars_are_injected(self, adapter):
        adapter._create_model_service_deployment()

        container = _deployed_body(adapter).spec.template.spec.containers[0]
        env = {e.name: e.value for e in container.env}
        assert env["PG_HOST"] == "host.minikube.internal"
        assert env["PG_DB"] == "ecommerce"
        assert env["MAMMOUTH_AGENT_MODEL"] == "gpt-4.1"

    def test_root_path_and_tracking_uri_always_set(self, adapter):
        adapter._create_model_service_deployment()

        container = _deployed_body(adapter).spec.template.spec.containers[0]
        env = {e.name: e.value for e in container.env}
        assert env["ROOT_PATH"] == f"/deploy/{adapter.namespace}/{adapter.service_name}"
        assert "MLFLOW_TRACKING_URI" in env

    def test_secret_ref_points_to_expected_name(self, adapter):
        adapter._create_model_service_deployment()

        container = _deployed_body(adapter).spec.template.spec.containers[0]
        assert adapter.secret_name == f"{adapter.project_name}-{adapter.model_name}-secrets"
        assert len(container.env_from) == 1
        secret_ref = container.env_from[0].secret_ref
        assert secret_ref.name == adapter.secret_name
        assert secret_ref.optional is True

    def test_no_env_vars_still_deploys(self):
        with patch("backend.infrastructure.k8s_deployment.config.load_kube_config", return_value=None):
            from backend.infrastructure.k8s_agent_deployment_adapter import K8SAgentDeployment

            deployment = K8SAgentDeployment("proj", "agent", "1", "dash-uid")
            deployment.apps_api_instance = MagicMock()
            deployment._create_model_service_deployment()

            container = _deployed_body(deployment).spec.template.spec.containers[0]
            env_names = {e.name for e in container.env}
            assert env_names == {"ROOT_PATH", "MLFLOW_TRACKING_URI"}


class TestK8SAgentDeploymentSecret:
    def _adapter_with_secret_values(self, secret_values):
        from kubernetes.client.rest import ApiException

        from backend.infrastructure.k8s_agent_deployment_adapter import K8SAgentDeployment

        deployment = K8SAgentDeployment(
            project_name="proj",
            model_name="agent",
            model_version="1",
            dashboard_uid="dash-uid",
            secret_values=secret_values,
        )
        deployment.apps_api_instance = MagicMock()
        deployment.service_api_instance = MagicMock()
        deployment.service_api_instance.read_namespaced_secret.side_effect = ApiException(status=404)
        return deployment

    def test_secret_created_when_secret_values_given(self):
        with patch("backend.infrastructure.k8s_deployment.config.load_kube_config", return_value=None):
            deployment = self._adapter_with_secret_values({"MAMMOUTH_API_KEY": "sk-new"})

            deployment._create_model_service_deployment()

            deployment.service_api_instance.create_namespaced_secret.assert_called_once()
            call = deployment.service_api_instance.create_namespaced_secret.call_args
            assert call.args[0] == deployment.namespace
            secret_body = call.args[1]
            assert secret_body.metadata.name == deployment.secret_name
            assert secret_body.string_data == {"MAMMOUTH_API_KEY": "sk-new"}

    def test_secret_updated_when_it_already_exists(self):
        with patch("backend.infrastructure.k8s_deployment.config.load_kube_config", return_value=None):
            deployment = self._adapter_with_secret_values({"MAMMOUTH_API_KEY": "sk-new"})
            deployment.service_api_instance.read_namespaced_secret.side_effect = None
            deployment.service_api_instance.read_namespaced_secret.return_value = MagicMock()

            deployment._create_model_service_deployment()

            deployment.service_api_instance.replace_namespaced_secret.assert_called_once()
            deployment.service_api_instance.create_namespaced_secret.assert_not_called()

    def test_no_secret_call_when_no_secret_values_given(self):
        with patch("backend.infrastructure.k8s_deployment.config.load_kube_config", return_value=None):
            deployment = self._adapter_with_secret_values(None)

            deployment._create_model_service_deployment()

            deployment.service_api_instance.create_namespaced_secret.assert_not_called()
            deployment.service_api_instance.replace_namespaced_secret.assert_not_called()
