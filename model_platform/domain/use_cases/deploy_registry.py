import uuid

from model_platform import CURRENT_USER
from model_platform.domain.entities.event import Event
from model_platform.infrastructure.k8s_registry_deployment_adapter import K8SRegistryDeployment
from model_platform.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()


def deploy_registry(project_name: str) -> None:
    k8s_deployment = K8SRegistryDeployment(project_name)
    k8s_deployment.create_registry_deployment()
    EVENT_LOGGER.add_event(
        Event(action=deploy_registry.__name__, user=uuid.UUID(CURRENT_USER), entity=project_name), project_name
    )
