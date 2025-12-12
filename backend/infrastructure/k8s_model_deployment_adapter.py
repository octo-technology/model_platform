import time

from kubernetes import client
from kubernetes.client.rest import ApiException
from loguru import logger

from backend.domain.ports.model_deployment_handler import ModelDeployment
from backend.infrastructure.k8s_deployment import K8SDeployment
from backend.utils import sanitize_project_name, sanitize_ressource_name


class K8SModelDeployment(ModelDeployment, K8SDeployment):
    def __init__(self, project_name: str, model_name: str, model_version: str, dashboard_uid: str):
        super().__init__()
        self.namespace = sanitize_project_name(project_name)
        self.docker_image_name = sanitize_project_name(f"{project_name}_{model_name}_{model_version}_ctr")
        self.service_name = sanitize_ressource_name(f"{project_name}-{model_name}-{model_version}-deployment")
        self.project_name = sanitize_project_name(project_name)
        self.model_name = sanitize_project_name(model_name)
        self.model_version = sanitize_project_name(model_version)
        self.dashboard_uid = dashboard_uid

    def create_model_deployment(self):
        logger.info(f"Creating model deployment in {self.namespace} namespace")
        self._create_or_update_namespace()  # TOUL dit : on devrait pas faire ça.
        self._create_or_update_model_service()
        self._create_model_service_deployment()
        return self.service_name

    def delete_model_deployment(self):
        logger.info(f"Deleting model deployment {self.service_name} in {self.namespace} namespace")
        self._delete_model_deployment()
        self._delete_model_service()

    def _create_or_update_model_service(self):
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=self.service_name,
                labels={"app": self.service_name},
            ),
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
            metadata=client.V1ObjectMeta(
                name=self.service_name,
                labels={
                    "app": self.service_name,
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                    "project_name": self.project_name,
                    "deployment_date": str(int(time.time())),
                    "dashboard_uid": self.dashboard_uid,
                },
            ),
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

        api = client.CustomObjectsApi()
        service_monitor = {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": f"{self.service_name}-monitor",
                "labels": {
                    "app": self.service_name,
                    "release": "kube-prometheus-stack",
                },
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": self.service_name,
                    }
                },
                "endpoints": [
                    {
                        "port": "http",
                        "path": "/metrics",
                        "interval": "30s",
                    }
                ],
                "namespaceSelector": {"matchNames": [self.namespace]},
            },
        }
        try:
            api.create_namespaced_custom_object(
                group="monitoring.coreos.com",
                version="v1",
                namespace="monitoring",
                plural="servicemonitors",
                body=service_monitor,
            )
            logger.info(f"✅ ServiceMonitor for {self.service_name} successfully created!")
        except ApiException as e:
            logger.error(f"❌ Error while creating ServiceMonitor: {e}")

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

    def _delete_model_service(self):
        try:
            api = client.CustomObjectsApi()
            api.delete_namespaced_custom_object(
                group="monitoring.coreos.com",
                version="v1",
                namespace="monitoring",
                plural="servicemonitors",
                name=f"{self.service_name}-monitor",
                body=client.V1DeleteOptions(),
            )
            logger.info(f"✅ ServiceMonitor for {self.service_name} successfully deleted!")
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"⚠️ ServiceMonitor for {self.service_name} not found, nothing to delete.")
            else:
                logger.error(f"⚠️ Error while deleting ServiceMonitor for {self.service_name}: {e}")
        try:
            self.service_api_instance.read_namespaced_service(self.service_name, self.namespace)
            self.service_api_instance.delete_namespaced_service(
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

    def _delete_model_deployment(self):
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
