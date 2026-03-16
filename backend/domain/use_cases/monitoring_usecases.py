"""Use cases for monitoring dashboard data retrieval.

Combines project and deployment information for monitoring dashboard.
"""

from typing import Any

from loguru import logger

from backend.domain.ports.project_db_handler import ProjectDbHandler
from backend.domain.use_cases.deployed_models import (
    list_deployed_models_with_status_for_a_project,
)
from backend.domain.use_cases.projects_usecases import list_projects


def get_monitoring_deployments(
    project_db_handler: ProjectDbHandler,
) -> list[dict]:
    """Get all deployed models across all projects for monitoring dashboard.

    Returns a list of deployed models with their project info for display
    in the monitoring dashboard. Each model includes basic info like name,
    version, deployment status, and links to Grafana dashboards.

    Parameters
    ----------
    project_db_handler : ProjectDbHandler
        Database handler for project queries

    Returns
    -------
    list[dict]
        List of deployed models with structure:
        {
            "id": "deployment_name",
            "name": "module_name",
            "version": "model_version",
            "project": "project_name",
            "deployment_name": "deployment_name",
            "status": "running|pending|error|unknown",
            "dashboard_url": "/grafana/d/...",
            "deployment_date": "ISO timestamp"
        }

    Raises
    ------
    Exception
        If database or K8s queries fail
    """
    try:
        # Get all projects
        projects = list_projects(project_db_handler)
        logger.debug(f"Found {len(projects)} projects")

        all_deployments = []

        # For each project, get deployed models
        for project in projects:
            project_name = project.get("name")
            if not project_name:
                logger.warning(f"Project missing 'name' field: {project}")
                continue

            try:
                deployments: list[Any] = list_deployed_models_with_status_for_a_project(project_name)
                logger.debug(f"Project '{project_name}': {len(deployments)} deployed models")

                # Reframe each deployment for monitoring dashboard
                for deployment in deployments:
                    # deployment is a dict from model_deployment.to_json()
                    model_entry = {
                        "id": deployment.get("deployment_name", "unknown"),  # Used for metrics API
                        "name": deployment.get("model_name", "Unknown"),
                        "version": deployment.get("version", 1),
                        "project": project_name,
                        "deployment_name": deployment.get("deployment_name", ""),
                        "status": deployment.get("status", "unknown"),
                        "dashboard_url": deployment.get("dashboard_url", ""),
                        "deployment_date": deployment.get("deployment_date", ""),
                    }
                    all_deployments.append(model_entry)

            except Exception as e:
                logger.warning(f"Failed to list deployments for project '{project_name}': {e}")
                continue

        logger.info(f"Monitoring: Retrieved {len(all_deployments)} deployed models " f"across {len(projects)} projects")
        return all_deployments

    except Exception as e:
        logger.error(f"Failed to retrieve monitoring deployments: {e}")
        raise


def get_monitoring_projects(
    project_db_handler: ProjectDbHandler,
) -> list[dict]:
    """Get list of all projects with basic metadata.

    Parameters
    ----------
    project_db_handler : ProjectDbHandler
        Database handler for project queries

    Returns
    -------
    list[dict]
        List of projects in format suitable for dropdown/filter UI
    """
    try:
        projects = list_projects(project_db_handler)
        logger.info(f"Retrieved {len(projects)} projects for monitoring")
        return projects
    except Exception as e:
        logger.error(f"Failed to retrieve projects for monitoring: {e}")
        raise
