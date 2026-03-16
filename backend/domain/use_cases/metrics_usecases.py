"""Business logic for metrics queries.

This module contains use cases for retrieving and aggregating metrics.
Use cases are isolated from HTTP concerns and can be tested independently.
"""

from typing import Optional

from loguru import logger

from backend.domain.entities.metrics import FleetMetrics, ModelMetrics
from backend.domain.ports.metrics_handler import MetricsHandler


async def get_model_metrics(model_id: str, period: str, metrics_handler: MetricsHandler) -> ModelMetrics:
    """Retrieve metrics for a single deployed model.

    Business logic:
    - Queries metrics handler for raw data
    - Validates data is available
    - Returns structured ModelMetrics entity

    Parameters
    ----------
    model_id : str
        Model deployment identifier
    period : str
        Time window (1d, 7d, 30d, 90d)
    metrics_handler : MetricsHandler
        Injected metrics data source adapter

    Returns
    -------
    ModelMetrics
        Structured metrics object

    Raises
    ------
    ValueError
        If model not found or has no metrics
    Exception
        If metrics handler fails
    """
    logger.debug(f"Fetching metrics for model={model_id}, period={period}")

    result = await metrics_handler.get_model_metrics(model_id, period)
    if not result:
        logger.warning(f"No metrics found for model {model_id}")
        raise ValueError(f"Model {model_id} not found or no metrics available")

    # Log warning if model has zero calls
    if result["total_calls"] == 0:
        logger.warning(f"Model {model_id} has zero calls in period {period}, " "check if model is actively used")

    # Validate data consistency
    if result["success_rate"] + result["error_rate"] > 101:
        logger.warning(
            f"Inconsistent rates for {model_id}: " f"success={result['success_rate']}%, error={result['error_rate']}%"
        )

    return ModelMetrics(
        model_id=model_id,
        project_name=result.get("project_name", ""),
        period=period,
        success_rate=result["success_rate"],
        error_rate=result["error_rate"],
        total_calls=result["total_calls"],
        total_errors=result["total_errors"],
    )


def get_fleet_metrics(
    project_name: Optional[str],
    period: str,
    metrics_handler: MetricsHandler,
) -> FleetMetrics:
    """Retrieve aggregate metrics for fleet overview.

    Business logic:
    - Queries all models' metrics
    - Categorizes by status (healthy/caution/alert)
    - Returns aggregated FleetMetrics

    Parameters
    ----------
    project_name : Optional[str]
        Filter by project, None for all projects
    period : str
        Time window
    metrics_handler : MetricsHandler
        Metrics data source

    Returns
    -------
    FleetMetrics
        Aggregate statistics

    Raises
    ------
    Exception
        If metrics handler fails
    """
    logger.debug(f"Fetching fleet metrics (project={project_name}, period={period})")

    metrics_list = metrics_handler.get_fleet_metrics(project_name, period)

    if not metrics_list:
        logger.warning(f"No models found in fleet/project {project_name}")
        return FleetMetrics(
            total_models=0,
            healthy_count=0,
            caution_count=0,
            alert_count=0,
            total_calls=0,
            period=period,
        )

    # Categorize by health status
    healthy = sum(1 for m in metrics_list if m["error_rate"] < 1.0)
    caution = sum(1 for m in metrics_list if 1.0 <= m["error_rate"] < 5.0)
    alert = sum(1 for m in metrics_list if m["error_rate"] >= 5.0)
    total_calls = sum(m["total_calls"] for m in metrics_list)

    logger.info(
        f"Fleet summary: {healthy} healthy, {caution} caution, {alert} alert " f"({len(metrics_list)} total models)"
    )

    return FleetMetrics(
        total_models=len(metrics_list),
        healthy_count=healthy,
        caution_count=caution,
        alert_count=alert,
        total_calls=total_calls,
        period=period,
    )
