"""Main entry point for the application.

This module starts the FastAPI application using Uvicorn.
"""

import uvicorn

from model_platform.adapters.http.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
