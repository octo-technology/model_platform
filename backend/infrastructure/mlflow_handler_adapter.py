import asyncio
import time

from loguru import logger
from mlflow import MlflowClient

from backend.domain.ports.registry_handler import RegistryHandler
from backend.infrastructure.mlflow_client import MLflowClientManager
from backend.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


class MLFlowHandlerAdapter(RegistryHandler):
    def __init__(
        self,
    ):
        self.cleaning_task = None
        self.client_pool: dict[str : dict[str : int | MlflowClient]] = {}
        self.start_cleaning_task()

    def get_registry_adapter(self, project_name: str, tracking_uri: str) -> MLFlowModelRegistryAdapter:
        if project_name not in self.client_pool:
            self._add_project_name_to_client_pool(project_name, tracking_uri)
        return self.client_pool[project_name]["registry"]

    def _add_project_name_to_client_pool(self, project_name, tracking_uri):
        logger.info(f"Connecting to project {project_name} registry with tracking URI {tracking_uri}")
        mlflow_client_manager = MLflowClientManager(tracking_uri=tracking_uri)
        mlflow_client_manager.initialize()
        registry_adapter = MLFlowModelRegistryAdapter(mlflow_client_manager=mlflow_client_manager)
        registry_and_ttl = {"registry": registry_adapter, "timestamp": int(time.time())}
        self.client_pool[project_name] = registry_and_ttl
        logger.info(f"Successfully connected to {project_name} project registry.")
        return registry_adapter

    def clean_client_pool(self, ttl_in_seconds: int = 300) -> None:
        current_timestamp: int = int(time.time())
        for project_name in list(self.client_pool.keys()):
            registry_and_ttl = self.client_pool[project_name]
            if current_timestamp - registry_and_ttl["timestamp"] > ttl_in_seconds:
                self._close_one_connexion(project_name)
            else:
                logger.info(f"Connection to {project_name} project registry is still valid.")

    def _close_one_connexion(self, project_name: str) -> None:
        self.client_pool[project_name]["registry"].mlflow_client_manager.close()
        self.client_pool.pop(project_name, None)
        logger.info(f"Closed connection to {project_name} project registry.")

    async def _clean_registry_pool_periodically(self, interval: int) -> None:
        """Tâche en arrière-plan pour nettoyer le pool de connexions MLflow."""
        self.running = True
        while self.running:
            await asyncio.sleep(interval)
            logger.info(f"🔄 Running periodic cleanup (interval={interval}s)")
            self.clean_client_pool(ttl_in_seconds=interval)

    def start_cleaning_task(self, interval: int = 60) -> None:
        self.cleaning_task = asyncio.create_task(self._clean_registry_pool_periodically(interval))
        logger.info(f"🟢 MLflow registry cleanup task started (every {interval} seconds)")

    async def _sync_model_infos_periodically(
        self,
        interval: int,
        project_db_handler,
        model_info_db_handler,
    ) -> None:
        from backend.domain.use_cases.model_info_usecases import sync_model_infos_for_project
        from backend.utils import sanitize_project_name

        while self.running:
            await asyncio.sleep(interval)
            logger.info(f"🔄 Syncing model_infos (interval={interval}s)")
            projects = project_db_handler.list_projects()
            for project in projects:
                tracking_uri = (
                    "http://"
                    + sanitize_project_name(project.name)
                    + "."
                    + sanitize_project_name(project.name)
                    + ".svc.cluster.local:5000"
                )
                try:
                    registry = self.get_registry_adapter(project.name, tracking_uri)
                    sync_model_infos_for_project(project.name, registry, model_info_db_handler)
                    # Evaluate deterministic compliance after sync
                    from backend.domain.use_cases.compliance_usecases import evaluate_project_compliance

                    evaluate_project_compliance(project.name, registry, model_info_db_handler)
                except Exception as e:
                    logger.warning(f"Could not sync model_infos for project {project.name}: {e}")

    def start_model_info_sync_task(
        self,
        interval: int,
        project_db_handler,
        model_info_db_handler,
    ) -> None:
        asyncio.create_task(self._sync_model_infos_periodically(interval, project_db_handler, model_info_db_handler))
        logger.info(f"🟢 model_infos sync task started (every {interval}s)")
