import os

from model_platform.domain.entities.docker.utils import build_image_from_context


class DockerfileTemplate:
    def __init__(self, base_image: str, env_file: str, workdir: str, python_version: str):
        self.base_image = base_image
        self.env_file = env_file
        self.workdir = workdir
        self.python_version = python_version
        self.dockerfile_template = """
        # Build an image that can serve mlflow models.
        FROM {base_image}

        {setup_python_venv}
        WORKDIR /opt/mlflow
        ENV GUNICORN_CMD_ARGS="--timeout 60 -k gevent"

        # granting read/write access and conditional execution authority to all child directories
        # and files to allow for deployment to AWS Sagemaker Serverless Endpoints
        # (see https://docs.aws.amazon.com/sagemaker/latest/dg/serverless-endpoints.html)
        RUN chmod o+rwX /opt/mlflow/

        # clean up apt cache to reduce image size
        RUN rm -rf /var/lib/apt/lists/*

        ENTRYPOINT ["python", "-c",]
        """

    def generate_dockerfile(self, output_dir: str) -> None:
        self.dockerfile_template = self.dockerfile_template.format(
            base_image=self._python_base_image(), setup_python_venv=self._setup_python_venv()
        )
        self._write_dockerfile(output_dir)

    def _write_dockerfile(self, output_dir: str):
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(self.dockerfile_template)

    def _python_base_image(self) -> str:
        return "python:{python_version}-slim".format(python_version=self.python_version)

    def _setup_python_venv(self) -> str:
        return "RUN apt-get -y update && apt-get install -y --no-install-recommends nginx"


if __name__ == "__main__":
    from model_platform import PROJECT_DIR

    os.environ["DOCKER_HOST"] = "unix:///Users/philippe.stepniewski/.colima/default/docker.sock"
    dockerfile = DockerfileTemplate(
        base_image="python:3.8-slim",
        env_file="env_file",
        workdir="/opt/mlflow",
        python_version="3.8",
    )
    context_path = os.path.join(PROJECT_DIR, "docker_test")
    dockerfile.generate_dockerfile(context_path)
    build_image_from_context(context_dir=context_path, image_name="mlflow_image")
