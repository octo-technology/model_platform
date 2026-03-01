import os

from kubernetes import client, config
from kubernetes.client import (
    ApiException,
    AppsV1Api,
    CoreV1Api,
)
from loguru import logger


class K8SDeployment:
    def __init__(
        self,
    ):
        if os.environ.get("KUBERNETES_SERVICE_HOST"):
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.service_api_instance: CoreV1Api = client.CoreV1Api()
        self.apps_api_instance: AppsV1Api = client.AppsV1Api()
        self.ingress_api_instance: client.NetworkingV1Api = client.NetworkingV1Api()
        self.host_name: str = os.environ["MP_HOST_NAME"]
        self.sub_path: str = os.environ["MP_DEPLOYMENT_PATH"]
        self.port: int = int(os.environ["MP_DEPLOYMENT_PORT"])
        self.namespace: str | None = None

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

    def delete_namespace(self):
        try:
            self.service_api_instance.read_namespace(name=self.namespace)
            logger.info(f"ℹ️ Namespace {self.namespace} found, deleting...")
            self.service_api_instance.delete_namespace(name=self.namespace)
            logger.info(f"✅ Namespace {self.namespace} successfully deleted!")
        except ApiException as e:
            if e.status == 404:
                logger.info(f"ℹ️ Namespace {self.namespace} not found, nothing to delete.")
            else:
                logger.error(f"⚠️ Error while deleting namespace {self.namespace}: {e}")
                raise
