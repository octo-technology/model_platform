import os
import shutil

from model_platform import PROJECT_DIR
from model_platform.domain.entities.docker.dockerfile_template import DockerfileTemplate
from model_platform.domain.entities.docker.utils import build_image_from_context
from tests.entities import TEST_DIR


def test_dockerfile_template_generate_dockerfile_should_correctly_build_image():
    dockerfile = DockerfileTemplate(
        python_version="3.9",
    )
    dockerfile.generate_dockerfile(os.path.join(TEST_DIR, "entities/docker_test"))
    context_path = os.path.join(TEST_DIR, "entities/docker_test")
    shutil.copyfile(
        os.path.join(PROJECT_DIR, "model_platform/domain/entities/docker/fast_api_template.py"),
        context_path + "/fast_api_template.py",
    )
    return_code = build_image_from_context(context_path, "test_image")
    assert return_code == 0
    os.remove(context_path + "/Dockerfile")
    os.remove(context_path + "/fast_api_template.py")
