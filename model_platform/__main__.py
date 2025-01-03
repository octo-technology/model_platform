"""Main entry point for the application.

This module starts the FastAPI application using Uvicorn.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("model_platform.api.app:app", host="0.0.0.0", port=8000, reload=True)
