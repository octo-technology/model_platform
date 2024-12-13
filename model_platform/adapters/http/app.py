"""Application module for the Model Platform API.

This module initializes the FastAPI application and includes the necessary routers.
"""

from fastapi import FastAPI

from model_platform.adapters.http.api import health_check, models_routes


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.
    """
    app = FastAPI(title="Model Platform API", version="1.0.0")
    app.include_router(health_check.router, prefix="/health", tags=["Health"])
    app.include_router(models_routes.router, prefix="/models", tags=["Models"])
    return app


app = create_app()
