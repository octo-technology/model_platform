# ruff: noqa: E501
import os

from loguru import logger

AGENT_BASE_IMAGE = "agent-base:latest"


class DockerfileTemplate:
    def __init__(self, python_version: str, use_agent_base_image: bool = False):
        self.python_version = python_version
        self.use_agent_base_image = use_agent_base_image
        self.dockerfile_template = """
        FROM {base_image}

        # Setup system package
        {setup_system_packages}

        # Set environment variables
        ENV IMAGE_NAME={image_name}
        ENV OTEL_METRICS_EXPORTER_LABELS="project_name={project_name},model_name={model_name},model_version={model_version}"
        ENV ROOT_PATH=""

        # Setup uv
        RUN which uv || (wget -qO- https://astral.sh/uv/install.sh | sh)
        ENV PATH="/root/.local/bin:$PATH"

        WORKDIR /opt/mlflow
        ENV GUNICORN_CMD_ARGS="--timeout 60 -k gevent"

        #Copy artefacts and dependencies lists
        COPY custom_model /opt/mlflow
        COPY fast_api_template.py /opt/mlflow
        COPY batch_predict_template.py /opt/mlflow
        # Install python model version

        RUN YAML_PYTHON_VERSION=$(grep -E "^ *- python=" /opt/mlflow/conda.yaml \
            | sed -E 's/.*python=([0-9]+\.[0-9]+).*/\\1/') && \
            echo "Python version from conda.yaml (minor): $YAML_PYTHON_VERSION" && \
            uv python install $YAML_PYTHON_VERSION

        # Install additional dependencies in the environment. --clear because the agent base image
        # already ships a .venv (bare `uv venv` errors out if one exists) built for a fixed Python
        # version — each agent's own conda.yaml can pin a different one, so the venv is always
        # recreated to match it. uv's package cache (separate from .venv, warmed by the base image)
        # is still reused for any matching wheels, so this stays cheaper than a bare python image.
        RUN uv venv --clear
        RUN uv pip install -r /opt/mlflow/requirements.txt
        RUN uv pip install uvicorn fastapi cloudpickle loguru mlflow python-multipart boto3
        RUN uv pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi \
            opentelemetry-exporter-prometheus

        # Clean up apt cache to reduce image size
        RUN rm -rf /var/lib/apt/lists/*
        EXPOSE 8000

        # Activate conda environment and start the application
        CMD ["bash", "-c", "uv run opentelemetry-instrument --service_name $IMAGE_NAME uvicorn fast_api_template:app --host 0.0.0.0 --port 8000 --root-path $ROOT_PATH --log-level debug"]
        """

    def generate_dockerfile(
        self, output_dir: str, image_name: str, project_name: str, model_name: str, version: str
    ) -> None:
        logger.info("Building Dockerfile")
        self.dockerfile_template = self.dockerfile_template.format(
            base_image=self._python_base_image(),
            setup_system_packages=self._setup_system_packages(),
            image_name=image_name,
            project_name=project_name,
            model_name=model_name,
            model_version=version,
        )
        self._write_dockerfile(output_dir)
        logger.info(f"Wrote Dockerfile to {output_dir}")

    def _write_dockerfile(self, output_dir: str):
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(self.dockerfile_template)

    def _python_base_image(self) -> str:
        if self.use_agent_base_image:
            return AGENT_BASE_IMAGE
        return "python:{python_version}-slim".format(python_version=self.python_version)

    def _setup_system_packages(self) -> str:
        if self.use_agent_base_image:
            # Already installed in the agent-base image (infrastructure/docker/agent-base.Dockerfile)
            return "# System packages already present in the agent base image"
        return """RUN apt-get update && apt-get install -y nginx curl \
        wget bzip2 libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*"""
