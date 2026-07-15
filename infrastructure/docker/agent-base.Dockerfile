FROM python:3.9-slim

# System packages shared by every agent image (same set as DockerfileTemplate._setup_system_packages)
RUN apt-get update && apt-get install -y nginx curl \
    wget bzip2 libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://astral.sh/uv/install.sh | sh && which uv || echo "UV installation failed"
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /opt/mlflow

# Pre-install the Python version and heavy deps common to every LangGraph agent so per-agent
# builds only need to resolve/install their own extra requirements on top of this layer.
RUN uv python install 3.9
RUN uv venv
RUN uv pip install \
    "mlflow>=3.0" langchain langchain-openai langgraph \
    uvicorn fastapi cloudpickle loguru python-multipart boto3 \
    opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-prometheus
