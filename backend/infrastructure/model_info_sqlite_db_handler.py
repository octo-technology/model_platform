# Philippe Stepniewski
import logging
import sqlite3

from backend.domain.entities.model_info import ModelInfo
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler


class ModelInfoDoesntExistError(Exception):
    def __init__(self, message, model_name=None, model_version=None, project_name=None):
        super().__init__(message)
        self.model_name = model_name
        self.model_version = model_version
        self.project_name = project_name


class ModelInfoAlreadyExistError(Exception):
    def __init__(self, message, model_name=None, model_version=None, project_name=None):
        super().__init__(message)
        self.model_name = model_name
        self.model_version = model_version
        self.project_name = project_name


def map_rows_to_model_infos(rows: list) -> list[ModelInfo]:
    return [
        ModelInfo(
            model_name=row[1],
            model_version=row[2],
            project_name=row[3],
            model_card=row[4],
            risk_level=row[5],
            generated_model_card=row[6] if len(row) > 6 else None,
            act_review=row[7] if len(row) > 7 else None,
            deterministic_compliance=row[8] if len(row) > 8 else "not_evaluated",
            llm_compliance=row[9] if len(row) > 9 else "not_evaluated",
        )
        for row in rows
    ]


class ModelInfoSQLiteDBHandler(ModelInfoDbHandler):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table_if_not_exists()

    def _init_table_if_not_exists(self):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS model_infos (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name    TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    project_name  TEXT NOT NULL,
                    model_card    TEXT,
                    risk_level    TEXT,
                    UNIQUE (model_name, model_version, project_name)
                )
                """
            )
            for col in ["generated_model_card", "act_review", "deterministic_compliance", "llm_compliance"]:
                try:
                    cursor.execute(f"ALTER TABLE model_infos ADD COLUMN {col} TEXT")
                except Exception:
                    pass
            connection.commit()
        finally:
            connection.close()

    def add_model_info(self, model_info: ModelInfo) -> bool:
        connection = sqlite3.connect(self.db_path)
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
            cursor.execute(
                """
                INSERT INTO model_infos (model_name, model_version, project_name, model_card, risk_level)
                VALUES (?, ?, ?, ?, ?)
                """,
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
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM model_infos WHERE model_name = ? AND model_version = ? AND project_name = ?",
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
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM model_infos WHERE project_name = ?",
                (project_name,),
            )
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_model_infos(rows)

    def update_model_card(self, model_name: str, model_version: str, project_name: str, model_card: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE model_infos SET model_card = ? WHERE model_name = ? AND model_version = ? AND project_name = ?",
                (model_card, model_name, model_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_generated_model_card(self, model_name: str, model_version: str, project_name: str, text: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE model_infos SET generated_model_card = ? "
                "WHERE model_name = ? AND model_version = ? AND project_name = ?",
                (text, model_name, model_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_risk_level(self, model_name: str, model_version: str, project_name: str, risk_level: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE model_infos SET risk_level = ? "
                "WHERE model_name = ? AND model_version = ? AND project_name = ?",
                (risk_level, model_name, model_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_act_review(self, model_name: str, model_version: str, project_name: str, text: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE model_infos SET act_review = ? "
                "WHERE model_name = ? AND model_version = ? AND project_name = ?",
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
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            updates = []
            values = []
            if deterministic_compliance is not None:
                updates.append("deterministic_compliance = ?")
                values.append(deterministic_compliance)
            if llm_compliance is not None:
                updates.append("llm_compliance = ?")
                values.append(llm_compliance)
            if not updates:
                return True
            values.extend([model_name, model_version, project_name])
            cursor.execute(
                f"UPDATE model_infos SET {', '.join(updates)} "
                "WHERE model_name = ? AND model_version = ? AND project_name = ?",
                values,
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def delete_model_info(self, model_name: str, model_version: str, project_name: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM model_infos WHERE model_name = ? AND model_version = ? AND project_name = ?",
                (model_name, model_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def search_model_infos(self, query: str, project_name: str | None = None) -> list[ModelInfo]:
        pattern = f"%{query}%"
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            if project_name:
                cursor.execute(
                    "SELECT * FROM model_infos WHERE project_name = ? AND (model_card LIKE ? OR risk_level LIKE ?)",
                    (project_name, pattern, pattern),
                )
            else:
                cursor.execute(
                    "SELECT * FROM model_infos WHERE model_card LIKE ? OR risk_level LIKE ?",
                    (pattern, pattern),
                )
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_model_infos(rows)
