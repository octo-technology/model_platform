import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("PATH_LOG_EVENTS", "/tmp/test_log_events")

from backend.domain.use_cases.deploy_agent import deploy_agent, remove_agent_deployment


def _fake_k8s_deployment_cluster(exists: bool = False):
    cluster = MagicMock()
    cluster.check_if_model_deployment_exists.return_value = exists
    return MagicMock(return_value=cluster)


class TestDeployAgent:
    def test_deploy_agent_injects_env_vars_from_deployment_config(self):
        agent_registry = MagicMock()
        agent_registry.get_deployment_config.return_value = {"PG_HOST": "host.minikube.internal"}
        k8s_agent_deployment_instance = MagicMock()
        k8s_agent_deployment_instance.service_name = "proj-my-agent-1-deployment"
        k8s_agent_deployment_cls = MagicMock(return_value=k8s_agent_deployment_instance)
        dashboard_handler = MagicMock()
        dashboard_handler.generate_dashboard_uid.return_value = "dash-uid"

        with patch("backend.domain.use_cases.deploy_agent.build_model_docker_image", return_value=1):
            deploy_agent(
                registry=MagicMock(),
                project_name="proj",
                agent_name="my_agent",
                version="1",
                dashboard_handler=dashboard_handler,
                current_user="user@example.com",
                agent_registry=agent_registry,
                k8s_deployment_cluster_cls=_fake_k8s_deployment_cluster(exists=False),
                k8s_agent_deployment_cls=k8s_agent_deployment_cls,
            )

        agent_registry.get_deployment_config.assert_called_once_with("my_agent", "1")
        k8s_agent_deployment_cls.assert_called_once_with(
            "proj", "my_agent", "1", "dash-uid", {"PG_HOST": "host.minikube.internal"}, None
        )
        k8s_agent_deployment_instance.create_model_deployment.assert_called_once()

    def test_deploy_agent_forwards_secret_values(self):
        k8s_agent_deployment_instance = MagicMock()
        k8s_agent_deployment_instance.service_name = "proj-my-agent-1-deployment"
        k8s_agent_deployment_cls = MagicMock(return_value=k8s_agent_deployment_instance)
        dashboard_handler = MagicMock()
        dashboard_handler.generate_dashboard_uid.return_value = "dash-uid"

        with patch("backend.domain.use_cases.deploy_agent.build_model_docker_image", return_value=1):
            deploy_agent(
                registry=MagicMock(),
                project_name="proj",
                agent_name="my_agent",
                version="1",
                dashboard_handler=dashboard_handler,
                secret_values={"MAMMOUTH_API_KEY": "sk-new"},
                k8s_deployment_cluster_cls=_fake_k8s_deployment_cluster(exists=False),
                k8s_agent_deployment_cls=k8s_agent_deployment_cls,
            )

        k8s_agent_deployment_cls.assert_called_once_with(
            "proj", "my_agent", "1", "dash-uid", {}, {"MAMMOUTH_API_KEY": "sk-new"}
        )

    def test_deploy_agent_without_agent_registry_still_deploys(self):
        k8s_agent_deployment_instance = MagicMock()
        k8s_agent_deployment_instance.service_name = "proj-my-agent-1-deployment"
        k8s_agent_deployment_cls = MagicMock(return_value=k8s_agent_deployment_instance)
        dashboard_handler = MagicMock()
        dashboard_handler.generate_dashboard_uid.return_value = "dash-uid"

        with patch("backend.domain.use_cases.deploy_agent.build_model_docker_image", return_value=1):
            deploy_agent(
                registry=MagicMock(),
                project_name="proj",
                agent_name="my_agent",
                version="1",
                dashboard_handler=dashboard_handler,
                k8s_deployment_cluster_cls=_fake_k8s_deployment_cluster(exists=False),
                k8s_agent_deployment_cls=k8s_agent_deployment_cls,
            )

        k8s_agent_deployment_cls.assert_called_once_with("proj", "my_agent", "1", "dash-uid", {}, None)

    def test_deploy_agent_skips_build_if_already_deployed(self):
        k8s_agent_deployment_cls = MagicMock()
        dashboard_handler = MagicMock()

        with patch("backend.domain.use_cases.deploy_agent.build_model_docker_image") as mock_build:
            result = deploy_agent(
                registry=MagicMock(),
                project_name="proj",
                agent_name="my_agent",
                version="1",
                dashboard_handler=dashboard_handler,
                k8s_deployment_cluster_cls=_fake_k8s_deployment_cluster(exists=True),
                k8s_agent_deployment_cls=k8s_agent_deployment_cls,
            )

        mock_build.assert_not_called()
        k8s_agent_deployment_cls.assert_not_called()
        assert result == 0

    def test_deploy_agent_does_not_deploy_on_build_failure(self):
        k8s_agent_deployment_cls = MagicMock()
        dashboard_handler = MagicMock()

        with patch("backend.domain.use_cases.deploy_agent.build_model_docker_image", return_value=0):
            deploy_agent(
                registry=MagicMock(),
                project_name="proj",
                agent_name="my_agent",
                version="1",
                dashboard_handler=dashboard_handler,
                k8s_deployment_cluster_cls=_fake_k8s_deployment_cluster(exists=False),
                k8s_agent_deployment_cls=k8s_agent_deployment_cls,
            )

        k8s_agent_deployment_cls.assert_not_called()


class TestRemoveAgentDeployment:
    def test_remove_agent_deployment_calls_delete(self):
        k8s_agent_deployment_instance = MagicMock()
        k8s_agent_deployment_cls = MagicMock(return_value=k8s_agent_deployment_instance)
        dashboard_handler = MagicMock()
        dashboard_handler.generate_dashboard_uid.return_value = "dash-uid"

        result = remove_agent_deployment(
            project_name="proj",
            agent_name="my_agent",
            version="1",
            dashboard_handler=dashboard_handler,
            k8s_agent_deployment_cls=k8s_agent_deployment_cls,
        )

        k8s_agent_deployment_cls.assert_called_once_with("proj", "my_agent", "1", "dash-uid")
        k8s_agent_deployment_instance.delete_model_deployment.assert_called_once()
        dashboard_handler.delete_dashboard.assert_called_once()
        assert result is True
