import datetime

from model_platform.domain.entities.docker.utils import build_model_docker_image
from model_platform.domain.entities.model_deployment import ModelDeployment
from model_platform.infrastructure.k8s_model_deployment_adapter import K8SModelDeployment
from model_platform.infrastructure.log_model_deploy_sqlite_adapter import SQLiteLogModelDeployment
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


def deploy_model(
    registry: MLFlowModelRegistryAdapter,
    deployed_models_sqlite_handler: SQLiteLogModelDeployment,
    project_name: str,
    model_name: str,
    version: str,
) -> None:
    if not deployed_models_sqlite_handler.model_deployment_already_exists(project_name, model_name, version):
        build_model_docker_image(registry, project_name, model_name, version)
        k8s_deployment = K8SModelDeployment(project_name, model_name, version)
        k8s_deployment.create_model_deployment()
        deployment_name = k8s_deployment.service_name
        model_deployment = ModelDeployment(
            project_name=project_name,
            model_name=model_name,
            version=version,
            deployment_name=deployment_name,
            deployment_date=str(datetime.datetime.now()),
        )
        deployed_models_sqlite_handler.add_deployment(model_deployment=model_deployment)


def remove_model_deployment(
    deployed_models_sqlite_handler: SQLiteLogModelDeployment, project_name: str, model_name: str, version: str
) -> None:
    """
    Removes the specified model and version from the Kubernetes cluster.

    Args:
        project_name (str): The name of the project.
        model_name (str): The name of the model.
        version (str): The version of the model.

    """
    k8s_deployment = K8SModelDeployment(project_name, model_name, version)
    k8s_deployment.delete_model_deployment()
    deployed_models_sqlite_handler.remove_deployment(project_name, model_name, version)
