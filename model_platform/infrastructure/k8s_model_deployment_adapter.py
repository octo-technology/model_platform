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
        self.service_name = None

    def create_model_deployment(self, project_name: str, model_name: str, version: str):
        self.service_name = f"{project_name}-{model_name}-{version}-deployment"
        self.service_name = sanitize_name(self.service_name)
        self.create_model_deployment_namespace()

    def create_model_deployment_namespace(self):
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(self.namespace))
        try:
            self.service_api_instance.create_namespace(namespace)
            print("Namespace 'models' successfully created.")
        except client.exceptions.ApiException as e:
            if e.status == 409:
                print("The namespace 'models' already exists.")
            else:
                print(f"Error: {e}")

    def create_model_service_deployment(self):
        pod_manifest = client.V1Pod(
            metadata=client.V1ObjectMeta(name="mon-pod", namespace=self.namespace, labels={"app": "mon-app"}),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name=self.service_name,
                        image=f"{self.service_name}:latest",
                        image_pull_policy="Never",
                        ports=[client.V1ContainerPort(container_port=8000)],
                    )
                ]
            ),
        )

        # Déploiement du Pod
        try:
            self.service_api_instance.create_namespaced_pod(namespace=self.namespace, body=pod_manifest)
            print("Pod 'mon-pod' déployé.")
        except client.exceptions.ApiException as e:
            print(f"Erreur lors du déploiement du Pod: {e}")

        # Définition du Service
        service_manifest = client.V1Service(
            metadata=client.V1ObjectMeta(name="mon-service", namespace=self.namespace),
            spec=client.V1ServiceSpec(
                selector={"app": "mon-app"},
                ports=[client.V1ServicePort(protocol="TCP", port=80, target_port=8080, node_port=30080)],
                type="NodePort",
            ),
        )

        # Déploiement du Service
        try:
            self.service_api_instance.create_namespaced_service(namespace=self.namespace, body=service_manifest)
            print("Service 'mon-service' créé avec NodePort 30080.")
        except client.exceptions.ApiException as e:
            print(f"Erreur lors du déploiement du Service: {e}")

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

    def _create_ingres_deployment(self):
        paths = [
            V1HTTPIngressPath(
                path=f"/{self.sub_path}/{self.service_name}/",
                path_type="Prefix",
                backend=V1IngressBackend(
                    service=V1IngressServiceBackend(name=self.service_name, port=V1ServiceBackendPort(number=self.port))
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

    def _add_path_to_ingress(self):
        existing_ingress = self.ingress_api_instance.read_namespaced_ingress(self.ingress_name, self.namespace)
        existing_paths = existing_ingress.spec.rules[0].http.paths if existing_ingress.spec.rules else []
        new_paths = [
            V1HTTPIngressPath(
                path=f"/{self.sub_path}/{self.service_name}/",
                path_type="Prefix",
                backend=client.V1IngressBackend(
                    service=client.V1IngressServiceBackend(
                        name=self.service_name, port=client.V1ServiceBackendPort(number=self.port)
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
