import os.path
import shutil
import time

from loguru import logger

from model_platform import PROJECT_DIR
from model_platform.domain.entities.docker.dockerfile_template import DockerfileTemplate
from model_platform.domain.entities.docker.utils import build_image_from_context
from model_platform.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


def recreate_directory(directory_path: str):
    """
    Recreates a directory at the specified path.

    If the directory already exists, it is removed and then recreated.

    Args:
        directory_path (str): The path of the directory to recreate.
    """
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
    os.makedirs(directory_path)


def remove_directory(directory_path: str):
    """
    Removes a directory at the specified path if it exists.

    Logs the removal action.

    Args:
        directory_path (str): The path of the directory to remove.
    """
    if os.path.exists(directory_path):
        logger.info("Removing {directory_path}")
        shutil.rmtree(directory_path)


def copy_fast_api_template_to_tmp_docker_folder(dest_path: str) -> None:
    """
    Copies the FastAPI template to the specified destination path.

    Args:
        dest_path (str): The destination path where the FastAPI template will be copied.
    """
    src_path = os.path.join(PROJECT_DIR, "model_platform/domain/entities/docker/fast_api_template.py")
    logger.info(f"Copying FastAPI template from {src_path} to {dest_path}")
    shutil.copy(src_path, dest_path)


def prepare_docker_context(registry: MLFlowModelRegistryAdapter, model_name: str, version: str) -> str:
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
    timestamp_id: int = int(time.time())
    dest_model_files = f"{timestamp_id}_{model_name}_{version}"
    path_dest = os.path.join(PROJECT_DIR, "tmp", dest_model_files)
    recreate_directory(path_dest)
    copy_fast_api_template_to_tmp_docker_folder(path_dest)
    registry.download_model_artifacts(model_name, version, path_dest)
    return path_dest


def build_docker_image_from_context_path(context_path: str, image_name: str) -> None:
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
    build_image_from_context(context_path, image_name)
    logger.info(f"Docker image {image_name} built successfully")
    remove_directory(context_path)


def generate_and_build_docker_image(registry: MLFlowModelRegistryAdapter, model_name: str, version: str) -> str:
    """
    Generates and builds a Docker image for the specified model and version.

    Args:
        registry (MLFlowModelRegistryAdapter): The model registry adapter to use for downloading model artifacts.
        model_name (str): The name of the model.
        version (str): The version of the model.

    Returns:
        str: The name of the built Docker image.
    """
    context_path: str = prepare_docker_context(registry, model_name, version)
    image_name: str = f"{model_name}_{version}_ctr"
    build_docker_image_from_context_path(context_path, image_name)
    return image_name
