import asyncio
import time

from loguru import logger
from mlflow import MlflowClient

from model_platform.domain.ports.registry_handler import RegistryHandler
from model_platform.infrastructure.mlflow_client import MLflowClientManager
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


class MLFlowHandlerAdapter(RegistryHandler):
    def __init__(
        self,
    ):
        self.client_pool: dict[str : dict[str : int | MlflowClient]] = {}
        self.cleaning_task = None
        self.running = False

    def connect(self, connexion_parameters: dict[str:str]) -> MLFlowModelRegistryAdapter:
        project_name: str = connexion_parameters["project_name"]
        tracking_uri: str = connexion_parameters["tracking_uri"]
        if project_name not in self.client_pool:
            logger.info(f"Connecting to project {project_name} registry with tracking URI {tracking_uri}")
            mlflow_client_manager = MLflowClientManager(tracking_uri=tracking_uri)
            mlflow_client_manager.initialize()
            registry_adapter = MLFlowModelRegistryAdapter(mlflow_client_manager=mlflow_client_manager)
            registry_and_ttl = {"registry": registry_adapter, "timestamp": int(time.time())}
            self.client_pool[project_name] = registry_and_ttl
            logger.info(f"Successfully connected to {project_name} project registry.")
        else:
            logger.info(f"Retrieving existing connection to {project_name} project registry.")
            registry_adapter = self.client_pool[project_name]["registry"]

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
        del self.client_pool[project_name]
        logger.info(f"Closed connection to {project_name} project registry.")

    async def _clean_registry_pool_periodically(self, interval: int) -> None:
        """Tâche en arrière-plan pour nettoyer le pool de connexions MLflow."""
        self.running = True
        while self.running:
            await asyncio.sleep(interval)
            logger.info(f"🔄 Running periodic cleanup (interval={interval}s)")
            self.clean_client_pool(ttl_in_seconds=interval)

    def start_cleaning_task(self, interval: int = 60) -> None:
        if self.cleaning_task is None:
            self.cleaning_task = asyncio.create_task(self._clean_registry_pool_periodically(interval))
            logger.info(f"🟢 MLflow registry cleanup task started (every {interval} seconds)")

    def stop_cleaning_task(self) -> None:
        if self.cleaning_task:
            self.running = False
            self.cleaning_task.cancel()
            try:
                asyncio.run(self.cleaning_task)
            except asyncio.CancelledError:
                pass
            self.cleaning_task = None
            logger.info("🔴 MLflow registry cleanup task stopped.")
