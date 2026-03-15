# Philippe Stepniewski
import logging

import psycopg2

from backend.domain.entities.model_info import ModelInfo
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.infrastructure.model_info_sqlite_db_handler import (
    ModelInfoAlreadyExistError,
    ModelInfoDoesntExistError,
    map_rows_to_model_infos,
)


class ModelInfoPostgresDBHandler(ModelInfoDbHandler):
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.db_config["dbname"] = "model_platform_db"
        self._init_table_if_not_exists()

    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def _init_table_if_not_exists(self):
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS model_infos (
                    id            SERIAL PRIMARY KEY,
                    model_name    TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    project_name  TEXT NOT NULL,
                    model_card    TEXT,
                    risk_level    TEXT,
                    UNIQUE (model_name, model_version, project_name)
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_model_infos_fts
                ON model_infos USING GIN (
                    to_tsvector('simple', COALESCE(model_card, '') || ' ' || COALESCE(risk_level, ''))
                )
                """
            )
            cursor.execute("ALTER TABLE model_infos ADD COLUMN IF NOT EXISTS generated_model_card TEXT")
            cursor.execute("ALTER TABLE model_infos ADD COLUMN IF NOT EXISTS act_review TEXT")
            cursor.execute(
                "ALTER TABLE model_infos ADD COLUMN IF NOT EXISTS deterministic_compliance TEXT DEFAULT 'not_evaluated'"
            )
            cursor.execute(
                "ALTER TABLE model_infos ADD COLUMN IF NOT EXISTS llm_compliance TEXT DEFAULT 'not_evaluated'"
            )
            connection.commit()
        finally:
            connection.close()

    def add_model_info(self, model_info: ModelInfo) -> bool:
        connection = self._connect()
        try:
            self.get_model_info(
                model_name=model_info.model_name,
                model_version=model_info.model_version,
                project_name=model_info.project_name,
            )
            raise ModelInfoAlreadyExistError(
                model_name=model_info.model_name,
                model_version=model_info.model_version,
                project_name=model_info.project_name,
                message="ModelInfo with same (model_name, model_version, project_name) already exists",
            )
        except ModelInfoDoesntExistError:
            logging.info("ModelInfo not found yet, ok")
        try:
            cursor = connection.cursor()
            query = """
                    INSERT INTO model_infos (model_name, model_version, project_name, model_card, risk_level)
                    VALUES (%s, %s, %s, %s, %s) \
                    """
            cursor.execute(
                query,
                (
                    model_info.model_name,
                    model_info.model_version,
                    model_info.project_name,
                    model_info.model_card,
                    model_info.risk_level,
                ),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def get_model_info(self, model_name: str, model_version: str, project_name: str) -> ModelInfo:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM model_infos WHERE model_name = %s AND model_version = %s AND project_name = %s",
                (model_name, model_version, project_name),
            )
            rows = cursor.fetchall()
        finally:
            connection.close()
        if len(rows) == 1:
            return map_rows_to_model_infos(rows)[0]
        raise ModelInfoDoesntExistError(
            message="ModelInfo doesn't exist",
            model_name=model_name,
            model_version=model_version,
            project_name=project_name,
        )

    def list_model_infos_for_project(self, project_name: str) -> list[ModelInfo]:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM model_infos WHERE project_name = %s",
                (project_name,),
            )
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_model_infos(rows)

    def update_model_card(self, model_name: str, model_version: str, project_name: str, model_card: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            query = (
                "UPDATE model_infos SET model_card = %s"
                " WHERE model_name = %s AND model_version = %s AND project_name = %s"
            )
            cursor.execute(query, (model_card, model_name, model_version, project_name))
            connection.commit()
        finally:
            connection.close()
            return True

    def update_generated_model_card(self, model_name: str, model_version: str, project_name: str, text: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE model_infos SET generated_model_card = %s "
                "WHERE model_name = %s AND model_version = %s AND project_name = %s",
                (text, model_name, model_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_act_review(self, model_name: str, model_version: str, project_name: str, text: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE model_infos SET act_review = %s "
                "WHERE model_name = %s AND model_version = %s AND project_name = %s",
                (text, model_name, model_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_compliance_statuses(
        self,
        model_name: str,
        model_version: str,
        project_name: str,
        deterministic_compliance: str | None = None,
        llm_compliance: str | None = None,
    ) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            updates = []
            values = []
            if deterministic_compliance is not None:
                updates.append("deterministic_compliance = %s")
                values.append(deterministic_compliance)
            if llm_compliance is not None:
                updates.append("llm_compliance = %s")
                values.append(llm_compliance)
            if not updates:
                return True
            values.extend([model_name, model_version, project_name])
            cursor.execute(
                f"UPDATE model_infos SET {', '.join(updates)} "
                "WHERE model_name = %s AND model_version = %s AND project_name = %s",
                values,
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def delete_model_info(self, model_name: str, model_version: str, project_name: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM model_infos WHERE model_name = %s AND model_version = %s AND project_name = %s",
                (model_name, model_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def search_model_infos(self, query: str, project_name: str | None = None) -> list[ModelInfo]:
        fts_condition = (
            "to_tsvector('simple', COALESCE(model_card, '') || ' ' || COALESCE(risk_level, ''))"
            " @@ websearch_to_tsquery('simple', %s)"
        )
        connection = self._connect()
        try:
            cursor = connection.cursor()
            if project_name:
                cursor.execute(
                    f"SELECT * FROM model_infos WHERE project_name = %s AND ({fts_condition})",
                    (project_name, query),
                )
            else:
                cursor.execute(
                    f"SELECT * FROM model_infos WHERE {fts_condition}",
                    (query,),
                )
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_model_infos(rows)
