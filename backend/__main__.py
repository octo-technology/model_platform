"""Main entry point for the application.

This module starts the FastAPI application using Uvicorn.
"""

import uvicorn

from backend.domain.use_cases.config import Config
from backend.dot_env import DotEnv

if __name__ == "__main__":
    DotEnv()
    Config()
    uvicorn.run("backend.api.app:app", host="0.0.0.0", port=8001, reload=True)
