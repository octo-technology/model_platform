"""Health Check API module.

This module provides a health check endpoint for the API.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health_check():
    """Health check endpoint.

    Returns
    -------
    dict
        A dictionary with the status of the API.
    """
    return {"status": "healthy"}
