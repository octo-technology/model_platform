import os
import re
import shutil
import subprocess
from datetime import datetime

from loguru import logger

from backend import PROJECT_DIR
from backend.domain.entities.docker.dockerfile_template import DockerfileTemplate
from backend.domain.use_cases.files_management import create_tmp_artefacts_folder, remove_directory
from backend.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


def _display_docker_build_logs(build_logs):
    for chunk in build_logs:
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                logger.info(line)


def build_image_from_context(context_dir: str, image_name: str) -> int:
    # Créer un nom de fichier de log basé sure le nom de l'image
    # Remplacer les caractères non autorisés dans les noms de fichiers
    safe_image_name = image_name.replace("/", "_").replace(":", "_")
    log_file_path = os.path.join(context_dir, f"docker_build_{safe_image_name}.log")

    docker_host = os.environ.get("DOCKER_HOST")
    logger.info(f"Process will use DOCKER_HOST= {docker_host} to build image")
    logger.info(f"Build logs will be written to {log_file_path}")

    # Préparer la commande docker
    cmd = ["docker", "build", "-t", image_name]

    # Ajouter l'option platform si nécessaire
    try:
        version_output = subprocess.check_output(["docker", "version", "--format", "{{.Server.Version}}"], text=True)
        major_version = int(version_output.split(".")[0])
        if major_version >= 19:
            #cmd.extend(["--platform", "linux/amd64"])
            cmd.extend(["--platform", "linux/arm64"])
    except Exception as e:
        logger.warning(f"Couldn't determine Docker version: {e}. Platform option might not be applied.")

    # Ajouter le chemin du contexte
    cmd.append(context_dir)

    # Ouvrir le fichier de log
    with open(log_file_path, "w") as log_file:
        # Écrire l'en-tête du log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"=== Docker Build for {image_name} started at {timestamp} ===\n")
        log_file.write(f"Command: {' '.join(cmd)}\n\n")

        # Exécuter la commande et streamer les logs en temps réel
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

            # Lire et logger la sortie en temps réel
            for line in process.stdout:
                stripped_line = line.strip()
                # Écrire dans le fichier de log
                log_file.write(f"{stripped_line}\n")
                log_file.flush()  # S'assurer que les logs sont écrits immédiatement
                # Également logger dans le logger standard
                logger.info(f"Build: {stripped_line}")

            # Attendre la fin du processus et vérifier le code de retour
            process.wait()

            # Écrire le résultat final dans le fichier de log
            timestamp_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if process.returncode == 0:
                result_message = f"Image '{image_name}' built successfully."
                log_file.write(f"\n=== Build completed successfully at {timestamp_end} ===\n")
            else:
                result_message = f"Docker build failed with return code {process.returncode}"
                log_file.write(f"\n=== Build failed at {timestamp_end} with return code {process.returncode} ===\n")

            logger.info(result_message)
            return 1 if process.returncode == 0 else 0

        except Exception as e:
            error_message = f"Error executing docker build: {e}"
            logger.error(error_message)
            log_file.write(f"\n=== ERROR: {error_message} ===\n")
            return 0


def copy_fast_api_template_to_tmp_docker_folder(dest_path: str) -> None:
    """
    Copies the FastAPI template to the specified destination path.

    Args:
        dest_path (str): The destination path where the FastAPI template will be copied.
    """
    src_path = os.path.join(PROJECT_DIR, "backend/domain/entities/docker/fast_api_template.py")
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
    if status == 0:
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


def sanitize_name(project_name: str) -> str:
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", project_name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    return sanitized_name


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
    image_name: str = sanitize_name(f"{project_name}_{model_name}_{version}_ctr")
    build_status = build_docker_image_from_context_path(context_path, image_name)
    if build_status:
        # clean_build_context(context_path)
        pass
    return build_status
