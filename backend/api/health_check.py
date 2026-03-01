"""Health Check API module.

This module provides a health check endpoint for the API.
"""

import os

import httpx
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

router = APIRouter()


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


@router.get("/")
def health_check():
    """Health check endpoint.

    Returns
    -------
    dict
        A dictionary with the status of the API.
    """
    return HealthCheck(status="OK")


@router.get("/storage")
def storage_health_check():
    """Check MinIO/S3 storage reachability from the backend.

    Uses the MinIO live health endpoint so the browser never has to reach
    an internal cluster URL directly.

    Returns
    -------
    dict
        {"status": "ok"} or {"status": "error", "detail": "..."}
    """
    s3_url = os.environ.get("MLFLOW_S3_ENDPOINT_URL", "")
    if not s3_url:
        return {"status": "error", "detail": "MLFLOW_S3_ENDPOINT_URL not configured"}
    try:
        response = httpx.get(f"{s3_url.rstrip('/')}/minio/health/live", timeout=3.0)
        if response.status_code == 200:
            return {"status": "ok"}
        return {"status": "error", "detail": f"HTTP {response.status_code}"}
    except Exception as e:
        logger.warning(f"Storage health check failed: {e}")
        return {"status": "error", "detail": str(e)}
