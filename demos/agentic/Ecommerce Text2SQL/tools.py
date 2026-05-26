"""LangChain tool factory for the SQL agent pipeline."""

from langchain_core.tools import tool

from .database_utils import format_rows
from .security import is_read_only_query


def validate_sql(query: str) -> str:
    """Return None if the query is valid read-only SQL, or an error message."""
    if not query or not query.strip():
        return "Error: empty query."
    if not is_read_only_query(query):
        return "Error: only SELECT/WITH queries are allowed (no INSERT/UPDATE/DELETE/DDL)."
    return None


def make_tools(adapter):
    """Return [get_schema, execute_sql] bound to the given DB adapter."""

    @tool
    def get_schema() -> str:
        """Fetch the full database schema: tables, columns and their types."""
        try:
            rows = adapter.fetch_schema_rows()
            if not rows:
                return "No schema found."
            schema: dict[str, list[str]] = {}
            for row in rows:
                col_info = f"{row['column_name']} ({row['data_type']})"
                schema.setdefault(row["table_name"], []).append(col_info)
            lines = []
            for table, columns in sorted(schema.items()):
                lines.append(f"{table}:")
                for col in columns:
                    lines.append(f"  - {col}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    @tool
    def execute_sql(query: str) -> str:
        """Execute a read-only SQL query and return the results as a formatted table."""
        error = validate_sql(query)
        if error:
            return error
        try:
            if isinstance(query, dict):
                query = query.get("query") or query.get("sql") or str(query)
            rows = adapter.execute_query(query)
            if not rows:
                return "Query executed, no results."
            return format_rows(rows, max_rows=500)
        except Exception as e:
            return f"SQL Error: {e}"

    return [get_schema, execute_sql]
