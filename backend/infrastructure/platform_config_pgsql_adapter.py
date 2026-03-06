# Philippe Stepniewski
import psycopg2

from backend.domain.ports.platform_config_handler import PlatformConfigHandler


class PlatformConfigPgsqlAdapter(PlatformConfigHandler):
    def __init__(self, db_config: dict):
        self.db_config = {**db_config, "dbname": "model_platform_db"}
        self._init_table_if_not_exists()

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def _init_table_if_not_exists(self):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS platform_config
                (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def get(self, key: str) -> str | None:
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT value FROM platform_config WHERE key = %s", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            connection.close()

    def set(self, key: str, value: str) -> None:
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO platform_config (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """,
                (key, value),
            )
            connection.commit()
        finally:
            connection.close()

    def delete(self, key: str) -> None:
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM platform_config WHERE key = %s", (key,))
            connection.commit()
        finally:
            connection.close()
