import os
import shutil

import pytest
from model_platform.domain.entities.docker.dockerfile_template import DockerfileTemplate
from model_platform.domain.entities.docker.utils import build_image_from_context
from tests.entities import TEST_DIR


def test_dockerfile_template_generate_dockerfile_should_correctly_build_image():
    dockerfile = DockerfileTemplate(
        python_version="3.9",
    )
    dockerfile.generate_dockerfile(os.path.join(TEST_DIR, "entities/docker_test"))
    context_path = os.path.join(TEST_DIR, "entities/docker_test")
    build_image_from_context(context_path, "test_image")
    assert True
    shutil.rmtree(context_path)
