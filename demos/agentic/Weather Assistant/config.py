"""Application settings for the weather assistant."""

import os

from dotenv import load_dotenv

# Look for a .env file next to this config.py, regardless of CWD
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


WEATHER_API_KEY = _get_env("WEATHER_API_KEY", "")
WEATHER_BASE_URL = _get_env("WEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")

MAMMOUTH_AGENT_MODEL = _get_env("MAMMOUTH_AGENT_MODEL", "gpt-4.1")
MAMMOUTH_TEMPERATURE = float(_get_env("MAMMOUTH_TEMPERATURE", "0"))
MAMMOUTH_API_KEY = _get_env("MAMMOUTH_API_KEY", "")
MAMMOUTH_BASE_URL = _get_env("MAMMOUTH_BASE_URL", "https://api.mammouth.ai/v1")
