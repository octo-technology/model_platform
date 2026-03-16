from abc import ABC, abstractmethod
from typing import Optional, TypedDict


class MetricsResult(TypedDict):
    """Return type for metrics queries.

    Attributes
    ----------
    success_rate : float
        Success rate percentage
    error_rate : float
        Error rate percentage
    total_calls : int
        Total API calls
    total_errors : int
        Total errors
    """

    success_rate: float
    error_rate: float
    total_calls: int
    total_errors: int


class MetricsHandler(ABC):
    """Abstract interface for metrics retrieval from time-series database.

    This handler abstracts metrics queries away from business logic,
    allowing different implementations (Prometheus, InfluxDB, etc.).
    """

    @abstractmethod
    async def get_model_metrics(self, model_id: str, period: str = "7d") -> Optional[MetricsResult]:
        """Query metrics for a single deployed model.

        Parameters
        ----------
        model_id : str
            Deployed model identifier (e.g., 'credit-v2-prod')
        period : str
            Time period for aggregation: '1d', '7d', '30d', '90d'

        Returns
        -------
        Optional[MetricsResult]
            Metrics dictionary or None if model not found

        Raises
        ------
        Exception
            If database connection fails or query times out
        """
        pass

    @abstractmethod
    async def get_fleet_metrics(self, project_name: Optional[str] = None, period: str = "7d") -> list[MetricsResult]:
        """Query aggregate metrics for fleet or specific project.

        Parameters
        ----------
        project_name : Optional[str]
            Filter by project name, None returns all projects
        period : str
            Time period for aggregation

        Returns
        -------
        list[MetricsResult]
            Metrics for each model in fleet/project

        Raises
        ------
        Exception
            If database connection fails
        """
        pass
