from loguru import logger

from model_platform.domain.entities.model_deployment import ModelDeployment
from model_platform.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter
from model_platform.infrastructure.k8s_registry_deployment_adapter import K8SRegistryDeployment
from model_platform.infrastructure.log_model_deploy_sqlite_adapter import SQLiteLogModelDeployment


def list_deployed_models_with_status_for_a_project(
    project_name: str, deployed_models_sqlite_handler: SQLiteLogModelDeployment
) -> list[dict]:
    deployed_models = deployed_models_sqlite_handler.list_deployed_models_for_project(project_name)
    logger.info(f"Deployed model list {deployed_models}")
    deployed_models_status = _get_models_deployment_status(project_name, deployed_models)
    return deployed_models_status


def _get_models_deployment_status(project_name: str, deployed_models_list: list) -> list:
    k8s_deployment_cluster = K8SDeploymentClusterAdapter()
    model_deployment: ModelDeployment
    model_deployment_status_list = []
    for model_deployment in deployed_models_list:
        status = k8s_deployment_cluster.is_service_deployed(model_deployment.deployment_name, project_name)
        model_deployment_status_list.append((model_deployment.deployment_name, status))
    return model_deployment_status_list


def remove_model_deployment_from_database(
    deployed_models_sqlite_handler: SQLiteLogModelDeployment, project_name: str, model_name: str, version: str
) -> None:
    deployed_models_sqlite_handler.remove_deployment(project_name, model_name, version)


def _remove_project_namespace(project_name: str) -> None:
    k8s_deployment = K8SRegistryDeployment(project_name)
    k8s_deployment.delete_namespace()
