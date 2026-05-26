"""E-commerce database utilities for query execution and formatting."""

from typing import Any

import psycopg

from .config import DB_CONFIG


def execute_query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute a parameterized query, return results as list of dicts."""
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            # psycopg treats % as a placeholder prefix — escape literal % when
            # there are no params (e.g. LLM-generated SQL with LIKE/ILIKE patterns)
            if not params:
                sql = sql.replace("%", "%%")
            cur.execute(sql, params)
            results = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [{columns[i]: row[i] for i in range(len(columns))} for row in results]


def format_rows(rows: list[dict[str, Any]], max_rows: int = 20) -> str:
    """Format query results as a text table."""
    if not rows:
        return "Aucun résultat."

    shown = rows[:max_rows]
    columns = list(shown[0].keys())
    lines = ["Résultats:"]
    lines.append(" | ".join(columns))
    lines.append("-" * 40)

    for row in shown:
        values = [str(row.get(col, "")) for col in columns]
        lines.append(" | ".join(values))

    if len(rows) > max_rows:
        lines.append(f"... +{len(rows) - max_rows} ligne(s)")

    return "\n".join(lines)
