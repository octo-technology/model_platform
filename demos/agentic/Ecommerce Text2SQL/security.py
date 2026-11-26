"""SQL query security validation."""

import re

FORBIDDEN_SQL_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "grant",
    "revoke",
    "copy",
    "vacuum",
    "call",
    "do",
    "execute",
}


def is_read_only_query(query: str) -> bool:
    """Return True if query is safe (SELECT/WITH only, single statement)."""
    cleaned = query.strip().lower()

    if not (cleaned.startswith("select") or cleaned.startswith("with")):
        return False

    if ";" in cleaned[:-1]:
        return False

    cleaned_no_strings = re.sub(r"'[^']*'", "''", cleaned)
    cleaned_no_strings = re.sub(r'"[^"]*"', '""', cleaned_no_strings)

    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if re.search(rf"\b{keyword}\b", cleaned_no_strings):
            return False

    return True
