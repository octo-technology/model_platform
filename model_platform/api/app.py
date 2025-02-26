"""Application module for the Model Platform API.

This module initializes the FastAPI application and includes the necessary routers.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from model_platform.api import auth_routes, deployed_models_routes, health_check, models_routes, projects_routes
from model_platform.infrastructure.mlflow_handler_adapter import MLFlowHandlerAdapter
from model_platform.infrastructure.project_sqlite_db_handler import ProjectSQLiteDBHandler
from model_platform.infrastructure.user_sqlite_db_adapter import UserSqliteDbAdapter


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
    app.state.project_sqlite_db_handler = ProjectSQLiteDBHandler(db_path=os.environ["PROJECTS_DB_PATH"])
    app.state.user_adapter = UserSqliteDbAdapter(db_path=os.environ["PROJECTS_DB_PATH"])
    app.state.task_status = {}
    app.state.registry_pool.start_cleaning_task(interval=60)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.
    """
    app = FastAPI(title="Model Platform API", version="1.0.0", lifespan=lifespan)
    app.include_router(health_check.router, prefix="/health", tags=["Health"])
    app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
    app.include_router(models_routes.router, prefix="/{project_name}/models", tags=["Models"])
    app.include_router(
        deployed_models_routes.router, prefix="/{project_name}/deployed_models", tags=["Deployed Models"]
    )
    app.include_router(projects_routes.router, prefix="/projects", tags=["Projects"])

    return app


app = create_app()
