import os


class DockerfileTemplate:
    def __init__(self, base_image: str, env_file: str, workdir: str, python_version: str):
        self.base_image = base_image
        self.env_file = env_file
        self.workdir = workdir
        self.python_version = python_version
        self.dockerfile_template = """
        # Build an image that can serve mlflow models.
        FROM {base_image}

        # Install packages
        {setup_system_packages}

        # Setup miniconda
        RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
            && /bin/bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda \
            && rm Miniconda3-latest-Linux-x86_64.sh
        ENV PATH /opt/conda/bin:$PATH

        WORKDIR /opt/mlflow
        ENV GUNICORN_CMD_ARGS="--timeout 60 -k gevent"

        # Install model and deps
        RUN conda update -n base -c defaults conda && conda clean --all --yes
        COPY conda.yaml /opt/mlflow
        RUN conda env create -f conda.yaml --prune

        ENV GUNICORN_CMD_ARGS="--timeout 60 -k gevent"

        # clean up apt cache to reduce image size
        RUN rm -rf /var/lib/apt/lists/*

        ENTRYPOINT ["python", "-c",]
        """

    def generate_dockerfile(self, output_dir: str) -> None:
        self.dockerfile_template = self.dockerfile_template.format(
            base_image=self._python_base_image(),
            setup_system_packages=self._setup_system_packages(),
        )
        self._write_dockerfile(output_dir)

    def _write_dockerfile(self, output_dir: str):
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(self.dockerfile_template)

    def _python_base_image(self) -> str:
        return "python:{python_version}-slim".format(python_version=self.python_version)

    def _setup_system_packages(self) -> str:
        return """RUN apt-get update && apt-get install -y \
                nginx \
                curl\
                wget \
                bzip2 \
                ca-certificates \
                && rm -rf /var/lib/apt/lists/*"""

    def _install_model_steps(self, model_dir: str) -> str:
        pass
