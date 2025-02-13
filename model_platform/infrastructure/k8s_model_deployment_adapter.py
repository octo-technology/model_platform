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

from model_platform.domain.ports.model_deployment_handler import ModelDeployment
from model_platform.dot_env import DotEnv
from model_platform.utils import sanitize_name


class K8SModelDeployment(ModelDeployment):

    def __init__(self, ingress_name: str = "deployment-ingress"):
        config.load_kube_config()
        self.service_api_instance: CoreV1Api = client.CoreV1Api()
        self.apps_api_instance: AppsV1Api = client.AppsV1Api()
        self.ingress_api_instance: client.NetworkingV1Api = client.NetworkingV1Api()
        self.ingress_name = ingress_name
        self.host_name = os.environ["MP_HOST_NAME"]
        self.sub_path = os.environ["MP_DEPLOYMENT_PATH"]
        self.port = int(os.environ["MP_DEPLOYMENT_PORT"])
        self.namespace = "models"

    def create_model_deployment(self, project_name: str, model_name: str, version: str):
        service_name = f"{project_name}-{model_name}-{version}-deployment"
        docker_image_name = f"{project_name}_{model_name}_{version}_ctr"
        service_name = sanitize_name(service_name)
        self.create_model_deployment_namespace()
        self._create_or_update_model_service(service_name)
        self._create_model_service_deployment(docker_image_name, service_name)
        if self._check_if_ingress_exists():
            self._add_path_to_ingress(service_name)
        else:
            self._create_ingres_deployment(service_name)

    def create_model_deployment_namespace(self):
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.namespace))  # Correction ici
        try:
            self.service_api_instance.create_namespace(namespace)
            print("Namespace 'models' successfully created.")
        except client.exceptions.ApiException as e:
            if e.status == 409:
                print("The namespace 'models' already exists.")
            else:
                print(f"Error: {e}")

    def _create_or_update_model_service(self, service_name: str):
        """Crée ou met à jour un service Kubernetes exposant MLflow."""

        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=service_name),
            spec=client.V1ServiceSpec(
                selector={"app": service_name},
                ports=[client.V1ServicePort(port=self.port, target_port=self.port, protocol="TCP", name="http")],
                type="NodePort",
            ),
        )
        try:
            self.service_api_instance.read_namespaced_service(service_name, self.namespace)
            self.service_api_instance.replace_namespaced_service(service_name, self.namespace, service)
            logger.info(f"✅ Service {service_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                self.service_api_instance.create_namespaced_service(self.namespace, service)
                logger.info(f"✅ Service {service_name} successfully created!")
            else:
                logger.info(f"⚠️ Error while creating/updating the service: {e}")

    def _create_model_service_deployment(self, docker_image_name: str, service_name: str):
        service_name = sanitize_name(service_name)

        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=service_name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": service_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": service_name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=service_name,
                                image=f"{docker_image_name}:latest",
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
            self.apps_api_instance.read_namespaced_deployment(service_name, self.namespace)
            self.apps_api_instance.replace_namespaced_deployment(
                namespace=self.namespace, name=service_name, body=deployment
            )
            logger.info(f"✅ Deployment {service_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                try:
                    self.apps_api_instance.create_namespaced_deployment(namespace=self.namespace, body=deployment)
                    logger.info(f"✅ Deployment {service_name} successfully created!")
                except ApiException as create_err:
                    logger.error(f"❌ Failed to create deployment {service_name}: {create_err}")
            else:
                logger.error(f"⚠️ Error while updating deployment {service_name}: {e}")

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

    def _create_ingres_deployment(self, service_name: str):
        service_name = sanitize_name(service_name)
        paths = [
            V1HTTPIngressPath(
                path=f"/{self.sub_path}/{service_name}/predict",
                path_type="Prefix",
                backend=V1IngressBackend(
                    service=V1IngressServiceBackend(name=service_name, port=V1ServiceBackendPort(number=self.port))
                ),
            )
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

    def _add_path_to_ingress(self, service_name: str):
        existing_ingress = self.ingress_api_instance.read_namespaced_ingress(self.ingress_name, self.namespace)
        existing_paths = existing_ingress.spec.rules[0].http.paths if existing_ingress.spec.rules else []
        new_paths = [
            V1HTTPIngressPath(
                path=f"/{self.sub_path}/{service_name}/predict",
                path_type="Prefix",
                backend=client.V1IngressBackend(
                    service=client.V1IngressServiceBackend(
                        name=service_name, port=client.V1ServiceBackendPort(number=self.port)
                    )
                ),
            )
        ]
        if new_paths:
            existing_paths.extend(new_paths)
            ingress_patch = {"spec": {"rules": [{"host": self.host_name, "http": {"paths": existing_paths}}]}}
            self.ingress_api_instance.patch_namespaced_ingress(
                name=self.ingress_name, namespace=self.namespace, body=ingress_patch
            )
            logger.info(f"✅ Ingress {self.host_name} successfully updated with new paths!")
        else:
            logger.info(f"ℹ️ No new paths to add. Ingress {self.host_name} remains unchanged.")


if __name__ == "__main__":
    DotEnv()
    k8s_model_deployment = K8SModelDeployment()
    k8s_model_deployment.create_model_deployment("foo", "mlflow_explo_titanic", "1")
