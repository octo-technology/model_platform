"""Database adapters — abstract the backend so tools work with any DB."""

import sqlite3
from typing import Any

from database_utils import execute_query as _pg_execute_query


class PostgresAdapter:
    """Adapter for the project's PostgreSQL database."""

    def fetch_schema_rows(self) -> list[dict]:
        return _pg_execute_query(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
        )

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        return _pg_execute_query(sql)


class SQLiteAdapter:
    """Adapter for a SQLite connection (e.g. Spider 2-Lite databases)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def fetch_schema_rows(self) -> list[dict]:
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cur.fetchall()]
        rows = []
        for table in tables:
            for col in self.conn.execute(f"PRAGMA table_info('{table}')").fetchall():
                rows.append(
                    {
                        "table_name": table,
                        "column_name": col[1],
                        "data_type": col[2] or "TEXT",
                    }
                )
        return rows

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        cur = self.conn.execute(sql)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        return [{columns[i]: row[i] for i in range(len(columns))} for row in cur.fetchall()]
