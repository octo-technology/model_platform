import os

from model_platform import PROJECT_DIR
from model_platform.domain.entities.docker.dockerfile_template import DockerfileTemplate
from model_platform.domain.entities.docker.utils import build_image_from_context


def test_dockerfile_template_generate_dockerfile_should_correctly_build_image():

    dockerfile = DockerfileTemplate(
        base_image="python:3.8-slim",
        env_file="env_file",
        workdir="/opt/mlflow",
        python_version="3.8",
    )
    context_path = os.path.join(PROJECT_DIR, "docker_test")
    dockerfile.generate_dockerfile(context_path)
    status = build_image_from_context(context_dir=context_path, image_name="mlflow_image")
    assert status == 0
