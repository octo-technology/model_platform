"""Use cases for deploying / undeploying agents on K8s.

Mirrors deploy_model.py but uses K8SAgentDeployment which adds the env vars
needed by agents (MLFLOW_TRACKING_URI, LLM credentials).
"""

import time

from loguru import logger

from backend.domain.entities.docker.utils import build_model_docker_image
from backend.domain.entities.event import Event
from backend.domain.entities.model_deployment import ModelDeployment
from backend.domain.ports.dashboard_handler import DashboardHandler
from backend.infrastructure.k8s_agent_deployment_adapter import K8SAgentDeployment
from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter
from backend.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter
from backend.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()


def deploy_agent(
    registry: MLFlowModelRegistryAdapter,
    project_name: str,
    agent_name: str,
    version: str,
    dashboard_handler: DashboardHandler,
    current_user: str = None,
) -> int:
    """Build the Docker image from the MLflow agent and deploy as a K8s service."""
    k8s_deployment = K8SDeploymentClusterAdapter()
    if not k8s_deployment.check_if_model_deployment_exists(project_name, agent_name, version):
        # Reuse the ML model docker builder — the MLflow pyfunc/ResponsesAgent
        # builds the same way as any other registered model
        build_status = build_model_docker_image(registry, project_name, agent_name, version)
        logger.info(f"Build status for agent {project_name}/{agent_name}:{version}: {build_status}")
        if build_status == 1:
            dashboard_uid = dashboard_handler.generate_dashboard_uid(project_name, agent_name, version)
            k8s_agent_deployment = K8SAgentDeployment(project_name, agent_name, version, dashboard_uid)
            k8s_agent_deployment.create_model_deployment()
            deployment_name = k8s_agent_deployment.service_name
            agent_deployment = ModelDeployment(
                project_name=project_name,
                model_name=agent_name,
                model_version=version,
                deployment_name=deployment_name,
                deployment_date=int(time.time()),
                dashboard_uid=dashboard_uid,
            )
            EVENT_LOGGER.add_event(
                Event(action=deploy_agent.__name__, user=current_user, entity=agent_deployment), project_name
            )
            dashboard_handler.create_dashboard(project_name, agent_name, version, deployment_name, dashboard_uid)
        elif build_status == 0:
            logger.error(f"Docker build failed for agent {project_name}/{agent_name}:{version}")
    else:
        build_status = 0
        logger.info(f"Agent deployment already exists for {project_name}/{agent_name}:{version}")
    return build_status


def remove_agent_deployment(
    project_name: str,
    agent_name: str,
    version: str,
    dashboard_handler: DashboardHandler,
    current_user: str = None,
) -> bool:
    dashboard_uid = dashboard_handler.generate_dashboard_uid(project_name, agent_name, version)
    k8s_agent_deployment = K8SAgentDeployment(project_name, agent_name, version, dashboard_uid)
    k8s_agent_deployment.delete_model_deployment()
    dashboard_handler.delete_dashboard(project_name, agent_name, version, dashboard_uid)

    agent_deployment = ModelDeployment(
        project_name=project_name,
        model_name=agent_name,
        model_version=version,
        deployment_name="",
        deployment_date=0,
        dashboard_uid=dashboard_uid,
    )
    EVENT_LOGGER.add_event(
        Event(action=remove_agent_deployment.__name__, user=current_user, entity=agent_deployment),
        project_name,
    )
    return True
