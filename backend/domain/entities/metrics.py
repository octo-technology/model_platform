from datetime import datetime

from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    """Metrics for a single deployed model.

    Parameters
    ----------
    model_id : str
        Deployed model identifier
    project_name : str
        Project containing the model
    period : str
        Time window for aggregation (1d, 7d, 30d, 90d)
    success_rate : float
        Success rate percentage (0-100)
    error_rate : float
        Error rate percentage (0-100)
    total_calls : int
        Total API calls in period
    total_errors : int
        Total errors in period
    timestamp : datetime
        When metrics were collected
    """

    model_id: str
    project_name: str
    period: str = "7d"

    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    error_rate: float = Field(..., ge=0, le=100, description="Error rate percentage")
    total_calls: int = Field(..., ge=0, description="Total API calls")
    total_errors: int = Field(..., ge=0, description="Total errors")

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "model_id": "credit-v2-prod",
                "project_name": "Banking Finance",
                "period": "7d",
                "success_rate": 93.5,
                "error_rate": 6.5,
                "total_calls": 45000,
                "total_errors": 2925,
                "timestamp": "2026-03-13T10:30:00",
            }
        }

    def to_json(self) -> dict:
        return {
            "model_id": self.model_id,
            "project_name": self.project_name,
            "period": self.period,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "timestamp": self.timestamp.isoformat(),
        }


class FleetMetrics(BaseModel):
    """Aggregate metrics for fleet overview.

    Parameters
    ----------
    total_models : int
        Number of deployed models
    healthy_count : int
        Models with error_rate < 1%
    caution_count : int
        Models with 1% <= error_rate < 5%
    alert_count : int
        Models with error_rate >= 5%
    total_calls : int
        Total calls across all models
    period : str
        Time window for aggregation
    """

    total_models: int = Field(..., ge=0)
    healthy_count: int = Field(..., ge=0)
    caution_count: int = Field(..., ge=0)
    alert_count: int = Field(..., ge=0)
    total_calls: int = Field(..., ge=0)
    period: str = "7d"

    class Config:
        schema_extra = {
            "example": {
                "total_models": 6,
                "healthy_count": 5,
                "caution_count": 1,
                "alert_count": 0,
                "total_calls": 250000,
                "period": "7d",
            }
        }

    def to_json(self) -> dict:
        return {
            "total_models": self.total_models,
            "healthy_count": self.healthy_count,
            "caution_count": self.caution_count,
            "alert_count": self.alert_count,
            "total_calls": self.total_calls,
            "period": self.period,
        }
