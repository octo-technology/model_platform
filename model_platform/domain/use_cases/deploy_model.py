from model_platform.domain.entities.docker.utils import build_model_docker_image
from model_platform.infrastructure.k8s_model_deployment_adapter import K8SModelDeployment
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


def deploy_model(registry: MLFlowModelRegistryAdapter, project_name: str, model_name: str, version: str) -> None:
    """
    Deploys the specified model and version to the Kubernetes cluster.

    Args:
        registry (MLFlowModelRegistryAdapter): The model registry adapter to use for downloading model artifacts.
        project_name (str): The name of the project.
        model_name (str): The name of the model.
        version (str): The version of the model.

    """
    build_model_docker_image(registry, project_name, model_name, version)
    k8s_deployment = K8SModelDeployment(project_name, model_name, version)
    k8s_deployment.create_model_deployment()


def remove_model_deployment(project_name: str, model_name: str, version: str) -> None:
    """
    Removes the specified model and version from the Kubernetes cluster.

    Args:
        project_name (str): The name of the project.
        model_name (str): The name of the model.
        version (str): The version of the model.

    """
    k8s_deployment = K8SModelDeployment(project_name, model_name, version)
    k8s_deployment.delete_model_deployment()
