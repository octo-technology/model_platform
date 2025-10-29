import time

from loguru import logger

from backend.domain.entities.docker.utils import build_model_docker_image
from backend.domain.entities.event import Event
from backend.domain.entities.model_deployment import ModelDeployment
from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter
from backend.infrastructure.k8s_model_deployment_adapter import K8SModelDeployment
from backend.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter
from backend.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()


def deploy_model(
    registry: MLFlowModelRegistryAdapter, project_name: str, model_name: str, version: str, current_user: str = None
) -> int:
    k8s_deployment = K8SDeploymentClusterAdapter()
    if not k8s_deployment.check_if_model_deployment_exists(project_name, model_name, version):
        build_status = build_model_docker_image(registry, project_name, model_name, version)
        logger.info(f"Build status for project {project_name}, model {model_name}, version {version}: {build_status}")
        if build_status == 1:
            logger.info(f"Model build successful for {project_name}, model {model_name}, version {version}")
            k8s_deployment = K8SModelDeployment(project_name, model_name, version)
            k8s_deployment.create_model_deployment()
            deployment_name = k8s_deployment.service_name
            model_deployment = ModelDeployment(
                project_name=project_name,
                model_name=model_name,
                model_version=version,
                deployment_name=deployment_name,
                deployment_date=int(time.time()),
            )
            EVENT_LOGGER.add_event(
                Event(action=deploy_model.__name__, user=current_user, entity=model_deployment), project_name
            )
        elif build_status == 0:
            logger.error(f"Docker build failed for project {project_name}, model {model_name}, version {version}")
    else:
        build_status = 0
        logger.info(
            f"Model deployment already exists for project {project_name}, model {model_name}, version {version}"
        )
    return build_status


def remove_model_deployment(project_name: str, model_name: str, version: str, current_user: str = None) -> int:
    """
    Removes the specified model and version from the Kubernetes cluster.

    Args:
        project_name (str): The name of the project.
        model_name (str): The name of the model.
        version (str): The version of the model.
        current_user (str): The name of the user who is removing the model deployment.

    """
    k8s_deployment = K8SModelDeployment(project_name, model_name, version)
    k8s_deployment.delete_model_deployment()
    model_deployment = ModelDeployment(
        project_name=project_name,
        model_name=model_name,
        model_version=version,
        deployment_name="",
        deployment_date=0,
    )
    EVENT_LOGGER.add_event(
        Event(action=remove_model_deployment.__name__, user=current_user, entity=model_deployment),
        project_name,
    )
    return True
