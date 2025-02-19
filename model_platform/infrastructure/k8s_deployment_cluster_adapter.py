import os

from kubernetes import client, config
from kubernetes.client import (
    AppsV1Api,
    CoreV1Api,
)
from loguru import logger

from model_platform.domain.ports.deployment_cluster_handler import DeploymentClusterHandler


class K8SDeploymentClusterAdapter(DeploymentClusterHandler):

    def __init__(self):
        config.load_kube_config()
        self.service_api_instance: CoreV1Api = client.CoreV1Api()
        self.apps_api_instance: AppsV1Api = client.AppsV1Api()
        self.ingress_api_instance: client.NetworkingV1Api = client.NetworkingV1Api()
        self.host_name = os.environ["MP_HOST_NAME"]
        self.sub_path = os.environ["MP_DEPLOYMENT_PATH"]

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
