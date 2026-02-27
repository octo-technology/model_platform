from loguru import logger

from backend.domain.entities.model_deployment import ModelDeployment
from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter
from backend.infrastructure.k8s_registry_deployment_adapter import K8SRegistryDeployment
from backend.utils import sanitize_project_name


def list_deployed_models_with_status_for_a_project(project_name: str) -> list[str]:
    k8s_deployment_cluster = K8SDeploymentClusterAdapter()
    deployed_models: list[ModelDeployment] = k8s_deployment_cluster.list_deployments_for_project(project_name)
    logger.debug(f"Deployed model list {deployed_models}")
    deployed_models_json = [model_deployment.to_json() for model_deployment in deployed_models]
    return deployed_models_json


def get_registry_status_for_project(project_name: str) -> str:
    """Return the K8s deployment status of the MLflow registry for a project.

    Returns one of: 'running', 'pending', 'error', 'not_found'.
    """
    k8s = K8SDeploymentClusterAdapter()
    namespace = sanitize_project_name(project_name)
    try:
        deployments = k8s.apps_api_instance.list_namespaced_deployment(
            namespace=namespace, label_selector="type=model_registry"
        )
        if not deployments.items:
            return "not_found"
        return k8s._resolve_deployment_status(deployments.items[0].status)
    except Exception as e:
        logger.warning(f"Could not get registry status for {project_name}: {e}")
        return "error"


def _remove_project_namespace(project_name: str) -> None:
    k8s_deployment = K8SRegistryDeployment(project_name)
    k8s_deployment.delete_namespace()
    k8s_deployment.create_db_dropper_job()
