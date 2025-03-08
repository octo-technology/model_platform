import os
import shutil

import docker
from docker.errors import DockerException
from loguru import logger

from model_platform import PROJECT_DIR
from model_platform.domain.entities.docker.dockerfile_template import DockerfileTemplate
from model_platform.domain.use_cases.files_management import create_tmp_artefacts_folder, remove_directory
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


def _display_docker_build_logs(build_logs):
    for chunk in build_logs:
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                logger.info(line)


def build_image_from_context(context_dir: str, image_name: str) -> int:
    docker_host = os.environ.get("DOCKER_HOST")
    logger.info(f"Process will use DOCKER_HOST= {docker_host} to build image")
    try:
        client = docker.from_env()
        logger.info("Connected to docker env")
    except DockerException as e:
        logger.error(f"Could not connect to Docker daemon: {e}. Have you set DOCKER_HOST environment variable?")
        return 1

    # In Docker < 19, `docker build` doesn't support the `--platform` option
    is_platform_supported = int(client.version()["Version"].split(".")[0]) >= 19
    # Enforcing the AMD64 architecture build for Apple M1 users
    platform_option = "linux/amd64" if is_platform_supported else ""
    logger.info("Starting image build")
    try:
        _, build_logs = client.images.build(path=context_dir, tag=image_name, platform=platform_option)
        logger.info(f"Image '{image_name}' built successfully.")
        _display_docker_build_logs(build_logs)
        return 0
    except (docker.errors.BuildError, docker.errors.APIError) as e:
        logger.error(f"Docker build failed: {e}")
        return 1


def copy_fast_api_template_to_tmp_docker_folder(dest_path: str) -> None:
    """
    Copies the FastAPI template to the specified destination path.

    Args:
        dest_path (str): The destination path where the FastAPI template will be copied.
    """
    src_path = os.path.join(PROJECT_DIR, "model_platform/domain/entities/docker/fast_api_template.py")
    logger.info(f"Copying FastAPI template from {src_path} to {dest_path}")
    shutil.copy(src_path, dest_path)


def prepare_docker_context(
    registry: MLFlowModelRegistryAdapter, project_name: str, model_name: str, version: str
) -> str:
    """
    Prepares the Docker context by creating a temporary directory, copying the FastAPI template,
    and downloading the model artifacts.

    Args:
        registry (MLFlowModelRegistryAdapter): The model registry adapter to use for downloading model artifacts.
        model_name (str): The name of the model.
        version (str): The version of the model.

    Returns:
        str: The path to the prepared Docker context.
    """
    path_dest = create_tmp_artefacts_folder(model_name, project_name, version, path=os.path.join(PROJECT_DIR, "tmp"))
    copy_fast_api_template_to_tmp_docker_folder(path_dest)
    registry.download_model_artifacts(model_name, version, path_dest)
    return path_dest


def build_docker_image_from_context_path(context_path: str, image_name: str) -> int:
    """
    Builds a Docker image from the specified context path and image name.

    Args:
        context_path (str): The path to the Docker context.
        image_name (str): The name of the Docker image to build.
    """
    dockerfile = DockerfileTemplate(
        python_version="3.9",
    )
    dockerfile.generate_dockerfile(context_path)
    logger.info(f"Starting docker build in {context_path}")
    status = build_image_from_context(context_path, image_name)
    if status == 1:
        logger.error(f"Failed to build Docker image {image_name}")
    else:
        logger.info(f"Docker image {image_name} built successfully")
    return status


def clean_build_context(context_path: str) -> None:
    """
    Cleans the build context by removing the specified directory.

    Args:
        context_path (str): The path to the build context directory.
    """
    remove_directory(context_path)


def build_model_docker_image(
    registry: MLFlowModelRegistryAdapter, project_name: str, model_name: str, version: str
) -> int:
    """
    Generates and builds a Docker image for the specified model and version.

    Args:
        registry (MLFlowModelRegistryAdapter): The model registry adapter to use for downloading model artifacts.
        project_name: The name of the project.
        model_name (str): The name of the model.
        version (str): The version of the model.

    Returns:
        str: The name of the built Docker image.

    """
    context_path: str = prepare_docker_context(registry, project_name, model_name, version)
    image_name: str = f"{project_name}_{model_name}_{version}_ctr"
    build_status = build_docker_image_from_context_path(context_path, image_name)
    clean_build_context(context_path)
    return build_status
