import os

from kubernetes import client
from loguru import logger

from backend.domain.entities.model_deployment import ModelDeployment
from backend.domain.ports.deployment_cluster_handler import DeploymentClusterHandler
from backend.infrastructure.k8s_deployment import K8SDeployment
from backend.utils import sanitize_project_name


class K8SDeploymentClusterAdapter(DeploymentClusterHandler, K8SDeployment):

    def __init__(self):
        super().__init__()

    def get_status(self) -> bool:
        try:
            api_response = self.service_api_instance.list_component_status()
            unhealthy_components = []
            for component in api_response.items:
                name = component.metadata.name
                conditions = component.conditions
                for condition in conditions:
                    if condition.type == "Healthy" and condition.status != "True":
                        unhealthy_components.append((name, condition.status))
            if unhealthy_components:
                logger.info("Cluster in poor health. Defective components:")
                for name, status_value in unhealthy_components:
                    logger.info(f"- {name}: {status_value}")
                return False
            else:
                logger.info("Cluster in good health.")
                return True
        except client.ApiException as e:
            logger.info(f"Error retrieving component status: {e}")
            return False

    def is_service_deployed(self, service_name, namespace):
        try:
            service = self.service_api_instance.read_namespaced_service(service_name, namespace)
            if service:
                logger.info(f"Service {service_name} in namespace {namespace} is available.")
                return True
            else:
                logger.info(f"Service {service_name} in namespace {namespace} not found.")
                return False
        except client.ApiException as e:
            logger.info(f"Error while retrieving service {service_name} in namespace {namespace}: {e}")
            return False

    def list_deployments_for_project(self, project_name: str) -> list[ModelDeployment]:
        project_name = sanitize_project_name(project_name)
        label_selector = f"project_name={project_name},type notin (model_registry)"
        deployments = self.apps_api_instance.list_namespaced_deployment(
            namespace=project_name, label_selector=label_selector
        )
        deployment_list = []
        for deployment in deployments.items:
            labels = deployment.metadata.labels
            labels["deployment_name"] = deployment.metadata.name
            deployment_list.append(ModelDeployment(**labels))
        return deployment_list

    def list_all_registries(self) -> list:
        registry_deployments = self.apps_api_instance.list_deployment_for_all_namespaces(
            label_selector="type=model_registry"
        )
        registry_deployment_list = []
        for registry in registry_deployments.items:
            logger.info(f"Registry found: {registry.metadata.name}")
            registry_deployment_list.append(registry)
        return registry_deployment_list

    def check_if_model_deployment_exists(self, project_name: str, model_name: str, model_version: str) -> bool:
        project_name = sanitize_project_name(project_name)
        label_selector = f"project_name={project_name},model_name={model_name},model_version={model_version}"
        deployments = self.apps_api_instance.list_namespaced_deployment(
            namespace=project_name, label_selector=label_selector
        )
        if deployments.items:
            return True
        return False

    def update_mlflow_s3_ip(self):
        local_ip = os.environ["LOCAL_IP"]
        new_env_value = f"http://{local_ip}:9000"

        for registry in self.list_all_registries():
            updated = False
            for container in registry.spec.template.spec.containers:
                for env_var in container.env:
                    if env_var.name == "MLFLOW_S3_ENDPOINT_URL":
                        env_var.value = new_env_value
                        updated = True
                        break

            if updated:
                patch_body = {
                    "spec": {"template": {"spec": {"containers": [{"name": container.name, "env": container.env}]}}}
                }

                self.apps_api_instance.patch_namespaced_deployment(
                    name=registry.metadata.name, namespace=registry.metadata.namespace, body=patch_body
                )
                print(f"✅ Mise à jour de {registry.metadata.name} avec {new_env_value}")
