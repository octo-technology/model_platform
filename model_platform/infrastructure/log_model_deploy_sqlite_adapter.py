import sqlite3

from loguru import logger

from model_platform.domain.entities.model_deployment import ModelDeployment
from model_platform.domain.ports.log_model_deploy_handler import LogModelDeployment


class SQLiteLogModelDeployment(LogModelDeployment):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table_model_deployments_if_not_exists()

    def add_deployment(self, model_deployment: ModelDeployment) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO model_deployments (project_name, model_name, version, deployment_name, deployment_date)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        model_deployment.project_name,
                        model_deployment.model_name,
                        model_deployment.version,
                        model_deployment.deployment_name,
                        str(model_deployment.deployment_date),
                    ),
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding deployment: {e}")
            return False

    def remove_deployment(self, project_name: str, model_name: str, version: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM model_deployments
                    WHERE project_name = ? AND model_name = ? AND version = ?
                """,
                    (project_name, model_name, version),
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error removing deployment: {e}")
            return False

    def remove_project_deployments(self, project_name: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM model_deployments
                    WHERE project_name = ?
                """,
                    (project_name,),
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error removing project deployments: {e}")
            return False

    def _init_table_model_deployments_if_not_exists(self):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS model_deployments (
                    project_name TEXT,
                    model_name TEXT,
                    version TEXT,
                    deployment_name TEXT,
                    deployment_date TEXT
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def _map_rows_to_model_deployment(self, rows: list) -> list[ModelDeployment]:
        return [
            ModelDeployment(
                project_name=row[0], model_name=row[1], version=row[2], deployment_name=row[3], deployment_date=row[4]
            )
            for row in rows
        ]

    def list_deployed_models_for_project(self, project_name: str) -> list:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM model_deployments
                    WHERE project_name = ?
                """,
                    (project_name,),
                )
                results = cursor.fetchall()
                return self._map_rows_to_model_deployment(results)
        except sqlite3.Error as e:
            logger.error(f"Error listing deployments: {e}")
            return []
