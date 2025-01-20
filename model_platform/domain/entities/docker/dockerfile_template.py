import os

from loguru import logger

from model_platform.domain.entities.docker.utils import build_image_from_context


class DockerfileTemplate:
    def __init__(self, python_version: str):
        self.python_version = python_version
        self.dockerfile_template = """
        FROM {base_image}

        # Setup system package
        {setup_system_packages}

        # Setup miniconda
        RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
            /bin/bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
            rm Miniconda3-latest-Linux-x86_64.sh
        ENV PATH /opt/conda/bin:$PATH

        WORKDIR /opt/mlflow
        ENV GUNICORN_CMD_ARGS="--timeout 60 -k gevent"

        # Install model and dependencies
        RUN conda update -n base -c defaults conda && conda clean --all --yes
        COPY custom_model/conda.yaml /opt/mlflow
        COPY custom_model/python_model.pkl /opt/mlflow
        RUN conda env create -f conda.yaml

        COPY fast_api_template.py /opt/mlflow
        # Install additional dependencies in the environment
        RUN /opt/conda/bin/conda install -n mlflow-env -c conda-forge uvicorn fastapi cloudpickle && \
            conda clean --all --yes

        # Clean up apt cache to reduce image size
        RUN rm -rf /var/lib/apt/lists/*

        EXPOSE 8000

        # Activate conda environment and start the application
        CMD ["bash", "-c", "source /opt/conda/bin/activate mlflow-env \
        && uvicorn fast_api_template:app --host 0.0.0.0 --port 8000"]

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
        wget bzip2 ca-certificates && rm -rf /var/lib/apt/lists/*"""

    def _install_model_steps(self, model_dir: str) -> str:
        pass


if __name__ == "__main__":
    from model_platform import PROJECT_DIR

    os.environ["DOCKER_HOST"] = "unix:///Users/philippe.stepniewski/.colima/default/docker.sock"
    dockerfile = DockerfileTemplate(
        python_version="3.9",
    )
    dockerfile.generate_dockerfile(os.path.join(PROJECT_DIR, "docker_test"))
    context_path = os.path.join(PROJECT_DIR, "docker_test")
    build_image_from_context(context_path, "test_image")
