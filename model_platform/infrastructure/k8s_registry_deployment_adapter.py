import os

from kubernetes import client, config
from kubernetes.client import AppsV1Api, CoreV1Api
from kubernetes.client.rest import ApiException
from loguru import logger

from model_platform.domain.ports.registry_deployment_handler import RegistryDeployment
from model_platform.utils import sanitize_name


class K8SRegistryDeployment(RegistryDeployment):

    def __init__(self, project_name: str):
        config.load_kube_config()
        self.service_api_instance: CoreV1Api = client.CoreV1Api()
        self.apps_api_instance: AppsV1Api = client.AppsV1Api()
        self.host_name = os.environ["MP_HOST_NAME"]
        self.sub_path = os.environ["MP_REGISTRY_PATH"]
        self.port = int(os.environ["MP_REGISTRY_PORT"])
        self.namespace = sanitize_name(project_name)
        self.project_name = sanitize_name(project_name)

    def create_registry_deployment(self):
        self._create_or_update_namespace()
        self._create_or_update_service(self.project_name)
        self._create_or_update_mlflow_deployment(self.project_name)

    def _create_or_update_namespace(self):
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

    def _create_or_update_service(self, project_name: str):
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=project_name),
            spec=client.V1ServiceSpec(
                selector={"app": project_name},
                ports=[client.V1ServicePort(port=self.port, target_port=self.port, protocol="TCP", name="http")],
                type="NodePort",
            ),
        )
        try:
            self.service_api_instance.read_namespaced_service(project_name, self.namespace)
            self.service_api_instance.replace_namespaced_service(project_name, self.namespace, service)
            logger.info(f"✅ Service {project_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                self.service_api_instance.create_namespaced_service(self.namespace, service)
                logger.info(f"✅ Service {project_name} successfully created!")
            else:
                logger.info(f"⚠️ Error while creating/updating the service: {e}")

    def _create_or_update_mlflow_deployment(self, project_name: str):
        """Crée ou met à jour un déploiement Kubernetes pour MLflow."""
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=project_name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": project_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": project_name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="mlflow",
                                image="ghcr.io/mlflow/mlflow:v2.9.2",
                                ports=[client.V1ContainerPort(container_port=self.port)],
                                env=[
                                    client.V1EnvVar(name="MLFLOW_SERVER_HOST", value="0.0.0.0"),
                                    client.V1EnvVar(name="MLFLOW_SERVER_PORT", value=str(self.port)),
                                    client.V1EnvVar(name="BACKEND_STORE_URI", value="sqlite:///mlflow.db"),
                                    client.V1EnvVar(name="ARTIFACT_STORE_URI", value="/mnt/artifacts"),
                                ],
                                command=[
                                    "mlflow",
                                    "server",
                                    "--host",
                                    "0.0.0.0",
                                    "--port",
                                    str(self.port),
                                    #  "--static-prefix",
                                    #  f"/{self.sub_path}/{project_name}",
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )

        try:
            self.apps_api_instance.read_namespaced_deployment(project_name, self.namespace)
            self.apps_api_instance.replace_namespaced_deployment(project_name, self.namespace, deployment)
            logger.info(f"✅ Deployment {project_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                self.apps_api_instance.create_namespaced_deployment(self.namespace, deployment)
                logger.info(f"✅ Deployment {project_name} successfully created!")
            else:
                logger.info(f"⚠️ Error while creating/updating the deployment: {e}")

    def delete_namespace(self):
        try:
            # Vérifier si le namespace existe
            self.service_api_instance.read_namespace(name=self.namespace)
            logger.info(f"ℹ️ Namespace {self.namespace} trouvé, suppression en cours...")

            # Supprimer le namespace
            self.service_api_instance.delete_namespace(name=self.namespace)
            logger.info(f"✅ Namespace {self.namespace} supprimé avec succès!")

        except ApiException as e:
            if e.status == 404:
                logger.info(f"ℹ️ Namespace {self.namespace} introuvable, rien à supprimer.")
            else:
                logger.error(f"⚠️ Erreur lors de la suppression du namespace {self.namespace}: {e}")
