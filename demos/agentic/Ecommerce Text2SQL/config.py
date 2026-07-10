"""Application settings for the chatbot."""

import os

from dotenv import load_dotenv

# Look for a .env file next to this config.py, regardless of CWD
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


DB_CONFIG = {
    "host": _get_env("PG_HOST", _get_env("PGHOST", "localhost")),
    "port": int(_get_env("PG_PORT", _get_env("PGPORT", "5432"))),
    "dbname": _get_env("PG_DB", _get_env("PGDATABASE", "ecommerce")),
    "user": _get_env("PG_USER", _get_env("PGUSER", "chatbot")),
    "password": _get_env("PG_PASSWORD", _get_env("PGPASSWORD", "chatbot")),
}

MAMMOUTH_AGENT_MODEL = _get_env("MAMMOUTH_AGENT_MODEL", "gpt-4.1")
MAMMOUTH_REFLECT_MODEL = _get_env("MAMMOUTH_REFLECT_MODEL", "codestral-2508")
MAMMOUTH_TEMPERATURE = float(_get_env("MAMMOUTH_TEMPERATURE", "0"))
MAMMOUTH_API_KEY = _get_env("MAMMOUTH_API_KEY", "")
MAMMOUTH_BASE_URL = _get_env("MAMMOUTH_BASE_URL", "https://api.mammouth.ai/v1")
