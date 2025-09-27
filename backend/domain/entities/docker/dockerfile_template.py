import os

from loguru import logger


class DockerfileTemplate:
    def __init__(self, python_version: str):
        self.python_version = python_version
        self.dockerfile_template = """
        FROM {base_image}

        # Setup system package
        {setup_system_packages}

        # Setup uv
        RUN wget -qO- https://astral.sh/uv/install.sh | sh && which uv || echo "UV installation failed"
        ENV PATH="/root/.local/bin:$PATH"

        WORKDIR /opt/mlflow
        ENV GUNICORN_CMD_ARGS="--timeout 60 -k gevent"

        #Copy artefacts and dependencies lists
        COPY custom_model /opt/mlflow
        COPY fast_api_template.py /opt/mlflow
        # Install python model version

        RUN YAML_PYTHON_VERSION=$(grep -E "^ *- python=" /opt/mlflow/conda.yaml \
            | sed -E 's/.*python=([0-9.]+).*/\\1/') && \
            echo "Python version from conda.yaml: $YAML_PYTHON_VERSION" && \
            uv python install $YAML_PYTHON_VERSION

        # Install additional dependencies in the environment
        RUN uv venv
        RUN uv pip install -r /opt/mlflow/requirements.txt
        RUN uv pip install uvicorn fastapi cloudpickle loguru mlflow python-multipart

        # Clean up apt cache to reduce image size
        RUN rm -rf /var/lib/apt/lists/*
        EXPOSE 8000

        # Activate conda environment and start the application
        CMD ["bash", "-c", "uv run uvicorn fast_api_template:app --host 0.0.0.0 --port 8000 --log-level debug"]
        """

    def generate_dockerfile(self, output_dir: str) -> None:
        logger.info("Building Dockerfile")
        self.dockerfile_template = self.dockerfile_template.format(
            base_image=self._python_base_image(),
            setup_system_packages=self._setup_system_packages(),
        )
        self._write_dockerfile(output_dir)
        logger.info(f"Wrote Dockerfile to {output_dir}")

    def _write_dockerfile(self, output_dir: str):
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(self.dockerfile_template)

    def _python_base_image(self) -> str:
        return "python:{python_version}-slim".format(python_version=self.python_version)

    def _setup_system_packages(self) -> str:
        return """RUN apt-get update && apt-get install -y nginx curl \
        wget bzip2 libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*"""
