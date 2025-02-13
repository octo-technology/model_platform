import os

from kubernetes import client, config
from kubernetes.client import (
    AppsV1Api,
    CoreV1Api,
    V1HTTPIngressPath,
    V1HTTPIngressRuleValue,
    V1Ingress,
    V1IngressBackend,
    V1IngressRule,
    V1IngressServiceBackend,
    V1IngressSpec,
    V1ServiceBackendPort,
)
from kubernetes.client.rest import ApiException
from loguru import logger

from model_platform.domain.ports.registry_deployment_handler import RegistryDeployment
from model_platform.dot_env import DotEnv
from model_platform.utils import sanitize_name


class K8SRegistryDeployment(RegistryDeployment):

    def __init__(self, ingress_name: str = "registry-ingress"):
        config.load_kube_config()
        self.service_api_instance: CoreV1Api = client.CoreV1Api()
        self.apps_api_instance: AppsV1Api = client.AppsV1Api()
        self.ingress_api_instance: client.NetworkingV1Api = client.NetworkingV1Api()
        self.ingress_name = ingress_name
        self.host_name = os.environ["MP_HOST_NAME"]
        self.sub_path = os.environ["MP_REGISTRY_PATH"]
        self.port = int(os.environ["MP_REGISTRY_PORT"])
        self.namespace = "default"

    def create_registry_deployment(self, project_name: str):
        project_name = sanitize_name(project_name)
        self._create_or_update_service(project_name)
        self._create_or_update_mlflow_deployment(project_name)
        if not self._check_if_ingress_exists():
            self._create_ingres_deployment(
                project_name,
            )

    def _check_if_ingress_exists(self):
        try:
            self.ingress_api_instance.read_namespaced_ingress(self.ingress_name, self.namespace)
            logger.info(f"Ingress {self.ingress_name} already exists!")
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            else:
                logger.info(f"⚠️ Error while checking if ingress exists: {e}")

    def _create_or_update_service(self, project_name: str):
        """Crée ou met à jour un service Kubernetes exposant MLflow."""

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

    def _create_ingres_deployment(self, project_name: str):
        paths = [
            V1HTTPIngressPath(
                path=f"/{self.sub_path}/",
                path_type="ImplementationSpecific",
                backend=V1IngressBackend(
                    service=V1IngressServiceBackend(name="nginx-reverse-proxy", port=V1ServiceBackendPort(number=80))
                ),
            ),
            V1HTTPIngressPath(
                path="/deploy/",
                path_type="ImplementationSpecific",
                backend=V1IngressBackend(
                    service=V1IngressServiceBackend(name="nginx-reverse-proxy", port=V1ServiceBackendPort(number=80))
                ),
            ),
        ]

        ingress = V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata={"name": self.ingress_name},
            spec=V1IngressSpec(
                # ingress_class_name="nginx",
                rules=[V1IngressRule(host=self.host_name, http=V1HTTPIngressRuleValue(paths=paths))],
            ),
        )
        try:
            self.ingress_api_instance.read_namespaced_ingress(self.ingress_name, self.namespace)
            self.ingress_api_instance.replace_namespaced_ingress(self.ingress_name, self.namespace, ingress)
            logger.info(f"✅ Ingress {self.host_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                self.ingress_api_instance.create_namespaced_ingress(namespace=self.namespace, body=ingress)
                logger.info(f"✅ Ingress {self.host_name} successfully created!")
            else:
                logger.info(f"⚠️ Error while creating/updating the ingress: {e}")

    def remove_mlflow_deployment(self, project_name: str):
        """Supprime le déploiement et le service Kubernetes associés à MLflow pour un project donné."""
        project_name = sanitize_name(project_name)

        try:
            self.apps_api_instance.delete_namespaced_deployment(name=project_name, namespace=self.namespace)
            logger.info(f"✅ Deployment {project_name} successfully deleted!")
        except ApiException as e:
            if e.status == 404:
                logger.info(f"ℹ️ Deployment {project_name} not found, skipping deletion.")
            else:
                logger.error(f"⚠️ Error while deleting deployment {project_name}: {e}")

        try:
            self.service_api_instance.delete_namespaced_service(name=project_name, namespace=self.namespace)
            logger.info(f"✅ Service {project_name} successfully deleted!")
        except ApiException as e:
            if e.status == 404:
                logger.info(f"ℹ️ Service {project_name} not found, skipping deletion.")
            else:
                logger.error(f"⚠️ Error while deleting service {project_name}: {e}")


if __name__ == "__main__":
    DotEnv()
    k8s_registry_deployment = K8SRegistryDeployment()
    k8s_registry_deployment.create_registry_deployment("foo")
