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
    Crée un dossier s'il n'existe pas, le supprime et le recrée s'il existe.

    Args:
        directory_path (str): Le chemin du dossier à vérifier et recréer.
    """
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)  # Supprime le dossier existent
    os.makedirs(directory_path)


def remove_directory(directory_path: str):
    """
    Supprime un dossier s'il existe.

    Args:
        directory_path (str): Le chemin du dossier à supprimer.
    """
    if os.path.exists(directory_path):
        logger.info("Removing {directory_path}")
        shutil.rmtree(directory_path)  # Supprime le dossier existent


def copy_fast_api_template_to_tmp_docker_folder(dest_path: str) -> None:
    src_path = os.path.join(PROJECT_DIR, "model_platform/domain/entities/docker/fast_api_template.py")
    logger.info(f"Copying FastAPI template from {src_path} to {dest_path}")
    shutil.copy(src_path, dest_path)


def prepare_docker_context(registry: MLFlowModelRegistryAdapter, model_name: str, version: str) -> str:
    timestamp_id: int = int(time.time())
    dest_model_files = f"{timestamp_id}_{model_name}_{version}"
    path_dest = os.path.join(PROJECT_DIR, "tmp", dest_model_files)
    recreate_directory(path_dest)
    copy_fast_api_template_to_tmp_docker_folder(path_dest)
    registry.download_model_artifacts(model_name, version, path_dest)
    return path_dest


def build_docker_image_from_context_path(context_path: str, image_name: str) -> None:
    dockerfile = DockerfileTemplate(
        python_version="3.9",
    )
    dockerfile.generate_dockerfile(context_path)
    logger.info(f"Starting docker build in {context_path}")
    build_image_from_context(context_path, image_name)
    logger.info(f"Docker image {image_name} built successfully")
    remove_directory(context_path)


def generate_and_build_docker_image(registry: MLFlowModelRegistryAdapter, model_name: str, version: str) -> str:
    context_path: str = prepare_docker_context(registry, model_name, version)
    image_name: str = f"{model_name}_{version}_ctr"
    build_docker_image_from_context_path(context_path, image_name)
    return image_name
