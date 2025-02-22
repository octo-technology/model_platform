import datetime
import uuid

from loguru import logger

from model_platform import CURRENT_USER
from model_platform.domain.entities.docker.utils import build_model_docker_image
from model_platform.domain.entities.event import Event
from model_platform.domain.entities.model_deployment import ModelDeployment
from model_platform.infrastructure.k8s_model_deployment_adapter import K8SModelDeployment
from model_platform.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter
from model_platform.infrastructure.log_model_deploy_sqlite_adapter import SQLiteLogModelDeployment
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()


def deploy_model(
    registry: MLFlowModelRegistryAdapter,
    deployed_models_sqlite_handler: SQLiteLogModelDeployment,
    project_name: str,
    model_name: str,
    version: str,
) -> None:
    if not deployed_models_sqlite_handler.model_deployment_already_exists(project_name, model_name, version):
        build_status = build_model_docker_image(registry, project_name, model_name, version)
        if build_status == 0:
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
            EVENT_LOGGER.add_event(
                Event(action=deploy_model.__name__, user=uuid.UUID(CURRENT_USER), entity=model_deployment), project_name
            )
        elif build_status == 1:
            logger.error("Docker build failed for project %s, model %s, version %s", project_name, model_name, version)
    else:
        build_status = 0
        logger.info(
            "Model deployment already exists for project %s, model %s, version %s", project_name, model_name, version
        )
    return build_status


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
    model_deployment = ModelDeployment(
        project_name=project_name,
        model_name=model_name,
        version=version,
        deployment_name="",
        deployment_date="",
    )
    EVENT_LOGGER.add_event(
        Event(action=remove_model_deployment.__name__, user=uuid.UUID(CURRENT_USER), entity=model_deployment),
        project_name,
    )
