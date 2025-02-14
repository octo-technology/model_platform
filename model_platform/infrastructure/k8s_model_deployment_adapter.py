import os

from kubernetes import client, config
from kubernetes.client import (
    AppsV1Api,
    CoreV1Api,
)
from kubernetes.client.rest import ApiException
from loguru import logger

from model_platform.domain.ports.model_deployment_handler import ModelDeployment
from model_platform.utils import sanitize_name


class K8SModelDeployment(ModelDeployment):

    def __init__(self, project_name: str, model_name: str, version: str):
        config.load_kube_config()
        self.service_api_instance: CoreV1Api = client.CoreV1Api()
        self.apps_api_instance: AppsV1Api = client.AppsV1Api()
        self.ingress_api_instance: client.NetworkingV1Api = client.NetworkingV1Api()
        self.host_name = os.environ["MP_HOST_NAME"]
        self.sub_path = os.environ["MP_DEPLOYMENT_PATH"]
        self.port = int(os.environ["MP_DEPLOYMENT_PORT"])
        self.namespace = sanitize_name(project_name)
        self.docker_image_name = f"{project_name}_{model_name}_{version}_ctr"
        self.service_name = sanitize_name(f"{project_name}-{model_name}-{version}-deployment")

    def create_model_deployment(self):
        logger.info(f"Creating model deployment in {self.namespace} namespace")
        self._create_or_update_namespace()
        self._create_or_update_model_service()
        self._create_model_service_deployment()

    def delete_model_deployment(self):
        logger.info(f"Deleting model deployment in {self.namespace} namespace")
        self._delete_model_service_deployment()

    def _create_or_update_namespace(self):
        """Crée un namespace si ce n'est pas déjà fait pour le project."""
        try:
            self.service_api_instance.read_namespace(self.namespace)
            logger.info(f"ℹ️ Namespace {self.namespace} already exists.")
        except ApiException as e:
            if e.status == 404:
                namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.namespace))
                self.service_api_instance.create_namespace(namespace)
                logger.info(f"✅ Namespace {self.namespace} successfully created!")
            else:
                logger.error(f"⚠️ Error while checking/creating the namespace: {e}")

    def _create_or_update_model_service(self):
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=self.service_name),
            spec=client.V1ServiceSpec(
                selector={"app": self.service_name},
                ports=[client.V1ServicePort(port=self.port, target_port=self.port, protocol="TCP", name="http")],
                type="NodePort",
            ),
        )
        try:
            self.service_api_instance.read_namespaced_service(self.service_name, self.namespace)
            self.service_api_instance.replace_namespaced_service(self.service_name, self.namespace, service)
            logger.info(f"✅ Service {self.service_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                self.service_api_instance.create_namespaced_service(self.namespace, service)
                logger.info(f"✅ Service {self.service_name} successfully created!")
            else:
                logger.info(f"⚠️ Error while creating/updating the service: {e}")

    def _create_model_service_deployment(self):
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=self.service_name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": self.service_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": self.service_name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=self.service_name,
                                image=f"{self.docker_image_name}:latest",
                                image_pull_policy="IfNotPresent",  # Ajouté pour éviter les erreurs de pull
                                ports=[client.V1ContainerPort(container_port=self.port)],
                            )
                        ],
                        restart_policy="Always",  # Bonne pratique pour un Deployment
                    ),
                ),
            ),
        )

        try:
            self.apps_api_instance.read_namespaced_deployment(self.service_name, self.namespace)
            self.apps_api_instance.replace_namespaced_deployment(
                namespace=self.namespace, name=self.service_name, body=deployment
            )
            logger.info(f"✅ Deployment {self.service_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                try:
                    self.apps_api_instance.create_namespaced_deployment(namespace=self.namespace, body=deployment)
                    logger.info(f"✅ Deployment {self.service_name} successfully created!")
                except ApiException as create_err:
                    logger.error(f"❌ Failed to create deployment {self.service_name}: {create_err}")
            else:
                logger.error(f"⚠️ Error while updating deployment {self.service_name}: {e}")

    def _delete_model_service_deployment(self):
        try:
            self.apps_api_instance.read_namespaced_deployment(self.service_name, self.namespace)
            self.apps_api_instance.delete_namespaced_deployment(
                name=self.service_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(),
            )
            logger.info(f"✅ Deployment {self.service_name} successfully deleted!")
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"⚠️ Deployment {self.service_name} not found, nothing to delete.")
            else:
                logger.error(f"⚠️ Error while deleting deployment {self.service_name}: {e}")
