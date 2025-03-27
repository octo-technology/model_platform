from loguru import logger

from backend.domain.entities.model_deployment import ModelDeployment
from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter
from backend.infrastructure.k8s_registry_deployment_adapter import K8SRegistryDeployment


def list_deployed_models_with_status_for_a_project(project_name: str) -> list[str]:
    k8s_deployment_cluster = K8SDeploymentClusterAdapter()
    deployed_models: list[ModelDeployment] = k8s_deployment_cluster.list_deployments_for_project(project_name)
    logger.debug(f"Deployed model list {deployed_models}")
    deployed_models_json = [model_deployment.to_json() for model_deployment in deployed_models]
    return deployed_models_json


def _remove_project_namespace(project_name: str) -> None:
    k8s_deployment = K8SRegistryDeployment(project_name)
    k8s_deployment.delete_namespace()
    k8s_deployment.create_db_dropper_job()
