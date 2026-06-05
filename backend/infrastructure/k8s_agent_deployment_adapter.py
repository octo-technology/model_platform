"""K8s deployment adapter for agentic models.

Subclass of K8SModelDeployment that injects the env vars needed by agents:
- MLFLOW_TRACKING_URI: so mlflow.langchain.autolog can send traces back
- MAMMOUTH_API_KEY / DB config: hardcoded MVP defaults (move to K8s Secret later)
"""

import time

from kubernetes import client
from kubernetes.client.rest import ApiException
from loguru import logger

from backend.infrastructure.k8s_model_deployment_adapter import K8SModelDeployment

# MVP-only hardcoded values. Move to K8s Secret in the project namespace later.
_MVP_HARDCODED_ENV = {
    "MAMMOUTH_API_KEY": "sk-4bMRoytWgpbwF0lp2Hs94w",
    "MAMMOUTH_BASE_URL": "https://api.mammouth.ai/v1",
    "MAMMOUTH_AGENT_MODEL": "gpt-4.1",
    "MAMMOUTH_REFLECT_MODEL": "codestral-2508",
    "MAMMOUTH_TEMPERATURE": "0",
    # Pointer to the e-commerce Postgres running on the host machine.
    # `host.minikube.internal` resolves to the host's IP from inside a minikube pod.
    "PG_HOST": "host.minikube.internal",
    "PG_PORT": "5432",
    "PG_DB": "ecommerce",
    "PG_USER": "chatbot",
    "PG_PASSWORD": "chatbot",
}


class K8SAgentDeployment(K8SModelDeployment):
    """K8s deployment for an agent. Reuses the ML deployment pattern but
    overrides the deployment spec to inject agent-specific env vars."""

    def _create_model_service_deployment(self):
        """Same shape as parent but with additional env vars for agents."""
        mlflow_tracking_uri = f"http://{self.namespace}.{self.namespace}.svc.cluster.local:5000"

        env_vars = [
            client.V1EnvVar(
                name="ROOT_PATH",
                value=f"/deploy/{self.namespace}/{self.service_name}",
            ),
            client.V1EnvVar(name="MLFLOW_TRACKING_URI", value=mlflow_tracking_uri),
        ]
        for key, value in _MVP_HARDCODED_ENV.items():
            env_vars.append(client.V1EnvVar(name=key, value=value))

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
