"""Metrics API routes.

Provides endpoints for retrieving real-time metrics from deployed models.
Requires authentication for fleet-level metrics.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from loguru import logger

from backend.domain.entities.metrics import FleetMetrics, ModelMetrics
from backend.domain.ports.metrics_handler import MetricsHandler
from backend.domain.ports.project_db_handler import ProjectDbHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases import metrics_usecases, monitoring_usecases
from backend.domain.use_cases.auth_usecases import (
    get_current_user,
    get_user_adapter,
)
from backend.domain.use_cases.user_usecases import (
    user_can_perform_action_for_project,
)
from backend.infrastructure.prometheus_adapter import PrometheusAdapter

router = APIRouter()


def get_metrics_handler() -> MetricsHandler:
    """Dependency injection for metrics handler.

    Returns
    -------
    MetricsHandler
        Prometheus adapter instance
    """
    return PrometheusAdapter()


def get_project_db_handler(request: Request) -> ProjectDbHandler:
    """Dependency injection for project database handler from app state.

    Returns
    -------
    ProjectDbHandler
        Project database handler instance
    """
    return request.app.state.project_db_handler


@router.get("/models/{model_id}", response_model=ModelMetrics)
async def get_model_metrics(
    model_id: str,
    period: str = Query("7d", regex="^(15m|30m|1h|6h|1d|7d|30d)$"),
    metrics_handler: MetricsHandler = Depends(get_metrics_handler),
) -> ModelMetrics:
    """Get real-time metrics for a single deployed model.

    Retrieves metrics from Prometheus for monitoring dashboard display.
    No authentication required for individual model metrics.

    Parameters
    ----------
    model_id : str
        Deployed model identifier (from K8s deployment)
    period : str
        Time window for aggregation: '1d', '7d', '30d', '90d' (default: '7d')
    metrics_handler : MetricsHandler
        Injected metrics handler (Prometheus adapter)

    Returns
    -------
    ModelMetrics
        Current metrics snapshot with success rate, error rate, calls, errors

    Raises
    ------
    404 Not Found
        If model not found in Prometheus
    503 Service Unavailable
        If Prometheus unavailable or query fails
    422 Unprocessable Entity
        If period parameter invalid

    Examples
    --------
    GET /api/metrics/models/credit-v2-prod?period=7d
    {
        "model_id": "credit-v2-prod",
        "project_name": "Banking Finance",
        "period": "7d",
        "success_rate": 93.5,
        "error_rate": 6.5,
        "total_calls": 45000,
        "total_errors": 2925,
        "timestamp": "2026-03-13T10:30:00"
    }
    """
    try:
        logger.debug(f"GET /api/metrics/models/{model_id}?period={period}")

        result = await metrics_usecases.get_model_metrics(
            model_id=model_id, period=period, metrics_handler=metrics_handler
        )
        logger.info(f"Retrieved metrics for {model_id}")
        return result

    except ValueError as e:
        logger.warning(f"Model not found: {model_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {e}")
        raise HTTPException(status_code=503, detail="Prometheus service unavailable")


@router.get("/fleet", response_model=FleetMetrics)
async def get_fleet_metrics(
    project_name: Optional[str] = None,
    period: str = Query("7d", regex="^(15m|30m|1h|6h|1d|7d|30d)$"),
    metrics_handler: MetricsHandler = Depends(get_metrics_handler),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> FleetMetrics:
    """Get aggregate metrics for fleet overview.

    Retrieves metrics for all deployed models (or specific project if specified).
    Categorizes models by health status (healthy/caution/alert).
    Requires authentication.

    Parameters
    ----------
    project_name : Optional[str]
        Filter by project name, None returns all projects
    period : str
        Time window: '1d', '7d', '30d', '90d' (default: '7d')
    metrics_handler : MetricsHandler
        Injected metrics handler
    current_user : dict
        Authenticated user from JWT token
    user_adapter : UserHandler
        User permissions adapter

    Returns
    -------
    FleetMetrics
        Aggregate statistics: counts by status, total calls

    Raises
    ------
    403 Forbidden
        If user lacks permission for project
    503 Service Unavailable
        If Prometheus unavailable
    422 Unprocessable Entity
        If period parameter invalid

    Examples
    --------
    GET /api/metrics/fleet?project_name=Banking&period=7d
    {
        "total_models": 6,
        "healthy_count": 5,
        "caution_count": 1,
        "alert_count": 0,
        "total_calls": 250000,
        "period": "7d"
    }
    """
    try:
        logger.debug(f"GET /api/metrics/fleet?project_name={project_name}&period={period}")

        # Check authorization if project specified
        if project_name:
            user_can_perform_action_for_project(
                current_user,
                project_name=project_name,
                action_name="get_fleet_metrics",
                user_adapter=user_adapter,
            )

        result = await metrics_usecases.get_fleet_metrics(
            project_name=project_name,
            period=period,
            metrics_handler=metrics_handler,
        )
        logger.info(f"Retrieved fleet metrics (project={project_name})")
        return result

    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        logger.error(f"Failed to retrieve fleet metrics: {e}")
        raise HTTPException(status_code=503, detail="Prometheus service unavailable")


@router.get("/monitoring/deployments")
async def get_monitoring_deployments(
    request: Request,
    project_db_handler: ProjectDbHandler = Depends(get_project_db_handler),
) -> list[dict]:
    """Get all deployed models for monitoring dashboard.

    Returns all models deployed across all projects with their metadata,
    status, and Grafana dashboard links. Used by monitoring frontend to
    populate the model catalog without authentication.

    Returns
    -------
    list[dict]
        List of deployed models with:
        - id: deployment identifier (for metrics API)
        - name: model name
        - version: model version
        - project: project name
        - deployment_name: K8s deployment name
        - status: running|pending|error|unknown
        - dashboard_url: link to Grafana dashboard

    Examples
    --------
    GET /api/metrics/monitoring/deployments

    [
        {
            "id": "credit-scoring-v2",
            "name": "CreditScoring",
            "version": 2,
            "project": "Finance",
            "deployment_name": "credit-scoring-v2-prod",
            "status": "running",
            "dashboard_url": "/d/abc123/credit-scoring"
        },
        ...
    ]
    """
    try:
        logger.debug("GET /api/metrics/monitoring/deployments")
        result = monitoring_usecases.get_monitoring_deployments(project_db_handler=project_db_handler)
        logger.info(f"Retrieved {len(result)} deployments for monitoring")
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve monitoring deployments: {e}")
        raise HTTPException(status_code=503, detail="Failed to retrieve deployments")


@router.get("/monitoring/projects")
async def get_monitoring_projects(
    request: Request,
    project_db_handler: ProjectDbHandler = Depends(get_project_db_handler),
) -> list[dict]:
    """Get all projects for monitoring dashboard filters.

    Returns list of all projects with basic metadata for use in
    dashboard project dropdown filters. No authentication required.

    Returns
    -------
    list[dict]
        List of projects with metadata

    Examples
    --------
    GET /api/metrics/monitoring/projects

    [
        {"name": "Finance", "description": "Banking models"},
        {"name": "Healthcare", "description": "Medical AI"},
        ...
    ]
    """
    try:
        logger.debug("GET /api/metrics/monitoring/projects")
        result = monitoring_usecases.get_monitoring_projects(project_db_handler=project_db_handler)
        logger.info(f"Retrieved {len(result)} projects for monitoring")
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve monitoring projects: {e}")
        raise HTTPException(status_code=503, detail="Failed to retrieve projects")
