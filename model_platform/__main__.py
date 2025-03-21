"""Main entry point for the application.

This module starts the FastAPI application using Uvicorn.
"""

import uvicorn

from model_platform.domain.use_cases.config import Config
from model_platform.dot_env import DotEnv

if __name__ == "__main__":
    DotEnv()
    Config()
    uvicorn.run("model_platform.api.app:app", host="0.0.0.0", port=8001, reload=True)
