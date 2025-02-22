from kubernetes import client
from loguru import logger

from model_platform.domain.ports.deployment_cluster_handler import DeploymentClusterHandler
from model_platform.infrastructure.k8s_deployment import K8SDeployment


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
