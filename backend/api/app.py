"""Application module for the Model Platform API.

This module initializes the FastAPI application and includes the necessary routers.
"""

import sys
from contextlib import asynccontextmanager

# Ugly stuff to remove ugly warning, sorry TOUL
import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api import (
    auth_routes,
    batch_routes,
    compliance_report_routes,
    demo_routes,
    deployed_models_routes,
    health_check,
    hugging_face_routes,
    llm_routes,
    metrics_routes,
    model_infos_routes,
    models_routes,
    projects_routes,
    users_routes,
)
from backend.domain.use_cases.config import Config
from backend.domain.use_cases.demo_usecases import SimulationManager
from backend.domain.use_cases.ds_simulation_usecases import DSSimulationManager
from backend.infrastructure.grafana_dashboard_adapter import GrafanaDashboardAdapter
from backend.infrastructure.k8s_batch_prediction_adapter import K8sBatchPredictionAdapter
from backend.infrastructure.minio_storage_adapter import MinioStorageAdapter
from backend.infrastructure.mlflow_handler_adapter import MLFlowHandlerAdapter
from backend.infrastructure.model_info_pgsql_db_handler import ModelInfoPostgresDBHandler
from backend.infrastructure.platform_config_pgsql_adapter import PlatformConfigPgsqlAdapter
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
    app.state.model_info_db_handler = ModelInfoPostgresDBHandler(db_config=config.pgsql_db_config)
    app.state.user_adapter = UserPgsqlDbAdapter(db_config=config.pgsql_db_config, admin_config=config.mp_admin_config)
    app.state.platform_config_handler = PlatformConfigPgsqlAdapter(db_config=config.pgsql_db_config)
    app.state.object_storage_handler = MinioStorageAdapter()
    app.state.dashboard_handler = GrafanaDashboardAdapter()
    app.state.batch_handler = K8sBatchPredictionAdapter()
    app.state.simulation_manager = SimulationManager()
    app.state.ds_simulation_manager = DSSimulationManager()
    app.state.task_status = {}
    app.state.registry_pool.start_cleaning_task(interval=60)
    app.state.registry_pool.start_model_info_sync_task(
        interval=30,
        project_db_handler=app.state.project_db_handler,
        model_info_db_handler=app.state.model_info_db_handler,
    )
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.
    """
    app = FastAPI(title="Model Platform API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://localhost:3000", "http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_check.router, prefix="/health", tags=["Health"])
    app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
    app.include_router(metrics_routes.router, prefix="/metrics", tags=["Metrics"])
    app.include_router(models_routes.router, prefix="/{project_name}/models", tags=["Models"])
    app.include_router(
        deployed_models_routes.router, prefix="/{project_name}/deployed_models", tags=["Deployed Models"]
    )
    app.include_router(projects_routes.router, prefix="/projects", tags=["Projects"])
    app.include_router(users_routes.router, prefix="/users", tags=["Users"])
    app.include_router(hugging_face_routes.router, prefix="/hugging_face", tags=["Registre"])
    app.include_router(model_infos_routes.router, prefix="/model_infos", tags=["Model Infos"])
    app.include_router(llm_routes.router, prefix="/ai", tags=["AI Assist"])
    app.include_router(compliance_report_routes.router, prefix="/compliance", tags=["Compliance Report"])
    app.include_router(batch_routes.router, prefix="/{project_name}/batch", tags=["Batch Predictions"])
    app.include_router(demo_routes.router, prefix="/demo", tags=["Demo Simulation"])
    return app


app = create_app()
