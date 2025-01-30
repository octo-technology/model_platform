"""Application module for the Model Platform API.

This module initializes the FastAPI application and includes the necessary routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from model_platform.api import deployed_models_routes, health_check, models_routes, projects_routes
from model_platform.infrastructure.mlflow_handler_adapter import MLFlowHandlerAdapter
from model_platform.infrastructure.project_sqlite_db_handler import ProjectSQLiteDBHandler

# Fix data to test front


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the lifespan of the FastAPI application.

    This context manager initializes the MLflow client when the application starts
    and closes it when the application shuts down.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.
    """
    app.state.registry_pool = MLFlowHandlerAdapter()
    app.state.project_sqlite_db_handler = ProjectSQLiteDBHandler(db_path="projects.db")
    app.state.task_status = {}
    yield
    app.state.registry_pool.clean_client_pool(ttl_in_seconds=0)
    app.state.task_status = None
    app.state.project_sqlite_db_handler = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.
    """
    app = FastAPI(title="Model Platform API", version="1.0.0", lifespan=lifespan)
    app.include_router(health_check.router, prefix="/health", tags=["Health"])
    app.include_router(models_routes.router, prefix="/{project_name}/models", tags=["Models"])
    app.include_router(deployed_models_routes.router, prefix="/deployed_models", tags=["Deployed Models"])
    app.include_router(projects_routes.router, prefix="/projects", tags=["Projects"])

    return app


app = create_app()
