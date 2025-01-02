"""Health Check API module.

This module provides a health check endpoint for the API.
"""

from fastapi import APIRouter
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
