import os.path

from model_platform import PROJECT_DIR
from model_platform.domain.entities.docker.utils import build_image_from_context


def test_build_image_from_context_with_basic_image_should_run_correctly():
    status = build_image_from_context(os.path.join(PROJECT_DIR, "tests/entities/basic_docker_test"), "test_image")
    assert status == 0
