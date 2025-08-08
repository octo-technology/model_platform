"""Application module for the Model Platform API.

This module initializes the FastAPI application and includes the necessary routers.
"""

import sys
from contextlib import asynccontextmanager

# Ugly stuff to remove ugly warning, sorry TOUL
import bcrypt
from fastapi import FastAPI
from loguru import logger

from backend.api import (
    auth_routes,
    deployed_models_routes,
    health_check,
    hugging_face_routes,
    models_routes,
    projects_routes,
    users_routes,
)
from backend.domain.use_cases.config import Config
from backend.infrastructure.mlflow_handler_adapter import MLFlowHandlerAdapter
from backend.infrastructure.project_pgsql_db_handler import ProjectPostgresDBHandler
from backend.infrastructure.user_psql_db_adapter import UserPgsqlDbAdapter

bcrypt.__about__ = bcrypt
# End of ugly stuff

logger.remove()  # remove the old handler. Else, the old one will work along with the new one you've added below'
logger.add(sys.stderr, level="INFO")


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
    config = Config()
    app.state.registry_pool = MLFlowHandlerAdapter()
    app.state.project_db_handler = ProjectPostgresDBHandler(db_config=config.pgsql_db_config)
    app.state.user_adapter = UserPgsqlDbAdapter(db_config=config.pgsql_db_config)
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
    app.include_router(users_routes.router, prefix="/users", tags=["Users"])
    app.include_router(hugging_face_routes.router, prefix="/hugging_face", tags=["Registre"])
    return app


app = create_app()
