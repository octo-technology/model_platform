"""K8s deployment adapter for agentic models.

Subclass of K8SModelDeployment that injects the env vars needed by agents:
- MLFLOW_TRACKING_URI: so mlflow.langchain.autolog can send traces back
- Non-secret deployment config (LLM base URL/model names, target DB host, ...):
  read from AgentInfo.env_vars, itself synced from the `deployment_env` MLflow tag
  set at agent registration (see register_agent.py and agent_info_usecases.py).
- Secrets (API keys, passwords): NEVER stored in code, DB, or MLflow tags. Passed in
  at deploy time (CLI/API `secret_values`) and pushed straight to a K8s Secret named
  `<project>-<agent>-secrets` via the Kubernetes API — this class never persists them
  anywhere else. If no `secret_values` are given (e.g. redeploying an existing agent),
  the existing Secret is left untouched. The Secret is referenced via envFrom with
  optional=True, so a deployment still succeeds (with those env vars simply absent)
  if it doesn't exist yet.
"""

import time

from kubernetes import client
from kubernetes.client.rest import ApiException
from loguru import logger

from backend.infrastructure.k8s_model_deployment_adapter import K8SModelDeployment


class K8SAgentDeployment(K8SModelDeployment):
    """K8s deployment for an agent. Reuses the ML deployment pattern but
    overrides the deployment spec to inject agent-specific env vars."""

    def __init__(
        self,
        project_name: str,
        model_name: str,
        model_version: str,
        dashboard_uid: str,
        env_vars: dict[str, str] | None = None,
        secret_values: dict[str, str] | None = None,
    ):
        super().__init__(project_name, model_name, model_version, dashboard_uid)
        self.env_vars = env_vars or {}
        self.secret_values = secret_values or {}
        self.secret_name = f"{self.project_name}-{self.model_name}-secrets"

    def _create_or_update_secret(self):
        """Push secret_values straight to a K8s Secret — never persisted anywhere else.

        Called only when secret_values were actually provided at deploy time; if the
        caller didn't pass any (e.g. redeploying an existing agent), any Secret already
        present in the namespace is left untouched."""
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=self.secret_name),
            string_data=self.secret_values,
        )
        try:
            self.service_api_instance.read_namespaced_secret(self.secret_name, self.namespace)
            self.service_api_instance.replace_namespaced_secret(self.secret_name, self.namespace, secret)
            logger.info(f"✅ Secret {self.secret_name} updated")
        except ApiException as e:
            if e.status == 404:
                self.service_api_instance.create_namespaced_secret(self.namespace, secret)
                logger.info(f"✅ Secret {self.secret_name} created")
            else:
                logger.error(f"⚠️ Error while creating/updating secret {self.secret_name}: {e}")

    def _create_model_service_deployment(self):
        """Same shape as parent but with additional env vars for agents."""
        if self.secret_values:
            self._create_or_update_secret()
        mlflow_tracking_uri = f"http://{self.namespace}.{self.namespace}.svc.cluster.local:5000"

        env_vars = [
            client.V1EnvVar(
                name="ROOT_PATH",
                value=f"/deploy/{self.namespace}/{self.service_name}",
            ),
            client.V1EnvVar(name="MLFLOW_TRACKING_URI", value=mlflow_tracking_uri),
        ]
        for key, value in self.env_vars.items():
            env_vars.append(client.V1EnvVar(name=key, value=value))
        env_from = [client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=self.secret_name, optional=True))]

        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=self.service_name,
                labels={
                    "app": self.service_name,
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                    "project_name": self.project_name,
                    "type": "agent",
                    "deployment_date": str(int(time.time())),
                    "dashboard_uid": self.dashboard_uid,
                },
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": self.service_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": self.service_name, "type": "agent"}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=self.service_name,
                                image=f"{self.docker_image_name}:latest",
                                image_pull_policy="IfNotPresent",
                                ports=[client.V1ContainerPort(container_port=self.port)],
                                env=env_vars,
                                env_from=env_from,
                            )
                        ],
                        restart_policy="Always",
                    ),
                ),
            ),
        )

        try:
            self.apps_api_instance.read_namespaced_deployment(self.service_name, self.namespace)
            self.apps_api_instance.replace_namespaced_deployment(
                namespace=self.namespace, name=self.service_name, body=deployment
            )
            logger.info(f"✅ Agent deployment {self.service_name} updated")
        except ApiException as e:
            if e.status == 404:
                try:
                    self.apps_api_instance.create_namespaced_deployment(namespace=self.namespace, body=deployment)
                    logger.info(f"✅ Agent deployment {self.service_name} created")
                except ApiException as create_err:
                    logger.error(f"❌ Failed to create agent deployment {self.service_name}: {create_err}")
            else:
                logger.error(f"⚠️ Error while updating agent deployment {self.service_name}: {e}")
