"""Application module for the Model Platform API.

This module initializes the FastAPI application and includes the necessary routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from model_platform.api import health_check, models_routes, deployed_models_routes
from model_platform.infrastructure.mlflow_client_manager import MLFLOW_CLIENT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan of the FastAPI application.

    This context manager initializes the MLflow client when the application starts
    and closes it when the application shuts down.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.
    """
    MLFLOW_CLIENT.initialize()
    yield
    MLFLOW_CLIENT.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.
    """
    app = FastAPI(title="Model Platform API", version="1.0.0", lifespan=lifespan)
    app.include_router(health_check.router, prefix="/health", tags=["Health"])
    app.include_router(models_routes.router, prefix="/models", tags=["Models"])
    app.include_router(deployed_models_routes.router, prefix="/deployed_models", tags=["Deployed Models"])

    return app


app = create_app()
