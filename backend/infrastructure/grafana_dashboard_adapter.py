import hashlib
import json
import re
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from loguru import logger

from backend.domain.ports.dashboard_handler import DashboardHandler
from backend.utils import sanitize_project_name


def extract_base_name(service_name: str) -> str:
    """Extract base name for Prometheus pod matching from K8s service_name.

    service_name comes from sanitize_ressource_name() and includes a 6-char hash.
    For cAdvisor metrics, we need to match pods without the hash suffix.

    Examples:
        "autonomous-vehicle-perception-credit-default-predictor-1-deployment-3fa669"
        -> "autonomous-vehicle-perception-credit-default-predictor-1-deployment"
    """
    # Remove the last 6-char hash suffix (added by sanitize_ressource_name)
    if len(service_name) > 7 and service_name[-7] == "-":
        return service_name[:-7]
    return service_name


class GrafanaDashboardAdapter(DashboardHandler):
    CONFIGMAP_NAMESPACE = "monitoring"
    DASHBOARD_LABEL_KEY = "grafana_dashboard"
    DASHBOARD_LABEL_VALUE = "1"
    TEMPLATE_PATH = Path(__file__).parent.parent / "domain" / "entities" / "grafana" / "predictions_dashboard.json"

    def __init__(self):
        self._load_k8s_config()
        self._v1 = client.CoreV1Api()

    def _load_k8s_config(self):
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            config.load_kube_config()
            logger.info("Loaded local Kubernetes config")

    def _get_configmap_name(self, dashboard_uid: str) -> str:
        return f"grafana-dashboard-{dashboard_uid}"

    def generate_dashboard_uid(self, project_name: str, model_name: str, version: str) -> str:
        """Generate a unique dashboard UID for Grafana (max 40 chars).

        Grafana dashboard UIDs have a strict 40 character limit.
        Format: sanitized_name[:33] + "-" + hash(6 chars) = max 40 chars
        """
        name = f"{project_name}-{model_name}-{version}"
        sanitized_name = re.sub(r"[^a-z0-9-]", "-", name.lower())
        sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Remove leading dashes
        sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Remove trailing dashes
        # Grafana UID limit is 40 chars: 33 chars + "-" + 6 chars hash
        return sanitized_name[:33] + "-" + hashlib.shake_256(bytes(sanitized_name, "utf-8")).hexdigest(3)

    def create_dashboard(
        self, project_name: str, model_name: str, version: str, service_name: str, dashboard_uid: str
    ) -> bool:
        try:
            if not self.TEMPLATE_PATH.exists():
                logger.error(f"Grafana dashboard template not found at {self.TEMPLATE_PATH}")
                return False

            with open(self.TEMPLATE_PATH, "r") as f:
                dashboard_json = json.load(f)

            dashboard_title = f"Predictions: {project_name}/{model_name}:{version}"

            dashboard_json["uid"] = dashboard_uid
            dashboard_json["title"] = dashboard_title

            # Get sanitized namespace for k8s metrics
            namespace = sanitize_project_name(project_name)

            # compute pattern strings up front
            base_name = extract_base_name(service_name)
            pod_pattern = f'pod=~"{base_name}.*"'
            container_pattern = f'container=~"{service_name}.*"'

            for panel in dashboard_json.get("panels", []):
                for target in panel.get("targets", []):
                    expr = target.get("expr")
                    if not expr:
                        continue

                    # namespace substitution applies to all k8s metrics
                    expr = expr.replace("{NAMESPACE}", namespace)

                    # choose proper placeholder replacement based on metric type
                    if "container_memory_usage_bytes" in expr or "container_cpu_usage_seconds_total" in expr:
                        expr = expr.replace('pod="{CONTAINER}"', pod_pattern)
                    elif "kube_pod_container_status_restarts_total" in expr:
                        expr = expr.replace('container="{CONTAINER}"', container_pattern)

                    # http metrics need a job filter
                    if "http_" in expr:
                        expr = expr.replace("{", f'{{job="{service_name}", ', 1)

                    target["expr"] = expr

            configmap_name = self._get_configmap_name(dashboard_uid)
            dashboard_filename = f"{dashboard_uid}.json"

            configmap = client.V1ConfigMap(
                api_version="v1",
                kind="ConfigMap",
                metadata=client.V1ObjectMeta(
                    name=configmap_name,
                    namespace=self.CONFIGMAP_NAMESPACE,
                    labels={
                        self.DASHBOARD_LABEL_KEY: self.DASHBOARD_LABEL_VALUE,
                        "app": "grafana",
                    },
                    annotations={
                        "grafana_folder": "Model Predictions",
                    },
                ),
                data={dashboard_filename: json.dumps(dashboard_json, indent=2)},
            )

            try:
                self._v1.read_namespaced_config_map(name=configmap_name, namespace=self.CONFIGMAP_NAMESPACE)
                self._v1.replace_namespaced_config_map(
                    name=configmap_name, namespace=self.CONFIGMAP_NAMESPACE, body=configmap
                )
                logger.info(f"Updated existing Grafana dashboard ConfigMap: {configmap_name}")
            except ApiException as e:
                if e.status == 404:
                    self._v1.create_namespaced_config_map(namespace=self.CONFIGMAP_NAMESPACE, body=configmap)
                    logger.info(f"Created Grafana dashboard ConfigMap: {configmap_name}")
                else:
                    raise

            logger.info(f"Successfully provisioned Grafana dashboard: {dashboard_uid}")
            return True

        except Exception as e:
            logger.error(f"Error creating Grafana dashboard ConfigMap: {e}")
            return False

    def delete_dashboard(self, project_name: str, model_name: str, version: str, dashboard_uid: str) -> bool:
        try:
            configmap_name = self._get_configmap_name(dashboard_uid)

            try:
                self._v1.delete_namespaced_config_map(name=configmap_name, namespace=self.CONFIGMAP_NAMESPACE)
                logger.info(f"Deleted Grafana dashboard ConfigMap: {configmap_name}")
                return True
            except ApiException as e:
                if e.status == 404:
                    logger.warning(f"ConfigMap {configmap_name} not found, nothing to delete")
                    return True
                else:
                    raise

        except Exception as e:
            logger.error(f"Error deleting Grafana dashboard ConfigMap: {e}")
            return False
