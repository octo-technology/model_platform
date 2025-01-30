"""Application module for the Model Platform API.

This module initializes the FastAPI application and includes the necessary routers.
"""

from fastapi import FastAPI

from model_platform.api import deployed_models_routes, health_check, models_routes, projects_routes


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
    app.include_router(deployed_models_routes.router, prefix="/deployed_models", tags=["Deployed Models"])
    app.include_router(projects_routes.router, prefix="/projects", tags=["Projects"])

    return app


app = create_app()
