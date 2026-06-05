"""List deployed agents for a project. Mirrors deployed_models.py."""

from loguru import logger

from backend.domain.entities.model_deployment import ModelDeployment
from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter


def list_deployed_agents_with_status_for_a_project(project_name: str) -> list[dict]:
    k8s = K8SDeploymentClusterAdapter()
    deployed: list[ModelDeployment] = k8s.list_agent_deployments_for_project(project_name)
    logger.debug(f"Deployed agents list: {deployed}")
    return [d.to_json() for d in deployed]
