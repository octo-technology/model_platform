import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime

from loguru import logger

from backend import PROJECT_DIR
from backend.domain.entities.docker.dockerfile_template import AGENT_BASE_IMAGE, DockerfileTemplate
from backend.domain.use_cases.files_management import create_tmp_artefacts_folder, remove_directory
from backend.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter


def _display_docker_build_logs(build_logs):
    for chunk in build_logs:
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                logger.info(line)


def get_build_platform() -> str:
    try:
        docker_info = subprocess.check_output(
            ["docker", "system", "info", "--format", "{{.Architecture}}"], text=True, stderr=subprocess.DEVNULL
        )
        docker_arch = docker_info.strip()
        if docker_arch in ["x86_64", "amd64"]:
            return "linux/amd64"
        elif docker_arch in ["aarch64", "arm64"]:
            return "linux/arm64"
    except subprocess.CalledProcessError:
        logger.warning("Could not detect Docker daemon architecture")


def build_image_from_context(context_dir: str, image_name: str, dockerfile_path: str | None = None) -> int:
    # Créer un nom de fichier de log basé sure le nom de l'image
    # Remplacer les caractères non autorisés dans les noms de fichiers
    safe_image_name = image_name.replace("/", "_").replace(":", "_")
    log_file_path = os.path.join(context_dir, f"docker_build_{safe_image_name}.log")

    docker_host = os.environ.get("DOCKER_HOST")
    logger.info(f"Process will use DOCKER_HOST= {docker_host} to build image")
    logger.info(f"Build logs will be written to {log_file_path}")

    # Préparer la commande docker
    cmd = ["docker", "build", "-t", image_name]
    if dockerfile_path:
        # Needed whenever the Dockerfile isn't named "Dockerfile" inside context_dir
        # (e.g. agent-base.Dockerfile), which is otherwise docker build's default lookup.
        cmd.extend(["-f", dockerfile_path])

    # Ajouter l'option platform si nécessaire
    try:
        version_output = subprocess.check_output(["docker", "version", "--format", "{{.Server.Version}}"], text=True)
        major_version = int(version_output.split(".")[0])
        if major_version >= 19:
            # Force la plateforme linux/amd64 pour la compatibilité avec minikube
            # cmd.extend(["--platform", "linux/arm64"])
            platform: str = get_build_platform()
            cmd.extend(["--platform", platform])
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


def copy_batch_predict_template_to_tmp_docker_folder(dest_path: str) -> None:
    """
    Copies the batch predict template to the specified destination path.

    Args:
        dest_path (str): The destination path where the batch predict template will be copied.
    """
    src_path = os.path.join(PROJECT_DIR, "backend/domain/entities/docker/batch_predict_template.py")
    logger.info(f"Copying batch predict template from {src_path} to {dest_path}")
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
    copy_batch_predict_template_to_tmp_docker_folder(path_dest)
    registry.download_model_artifacts(model_name, version, path_dest)
    return path_dest


def build_docker_image_from_context_path(
    context_path: str, image_name: str, project_name: str, model_name: str, version: str, is_agent: bool = False
) -> int:
    """
    Builds a Docker image from the specified context path and image name.

    Args:
        context_path (str): The path to the Docker context.
        image_name (str): The name of the Docker image to build.
        is_agent (bool): Whether this image is for an agent, in which case the build reuses the
            pre-built `agent-base` image (langgraph/langchain/mlflow/fastapi/otel already installed)
            instead of a bare Python image.
    """
    use_agent_base_image = is_agent and ensure_agent_base_image()
    dockerfile = DockerfileTemplate(
        python_version="3.9",
        use_agent_base_image=use_agent_base_image,
    )
    dockerfile.generate_dockerfile(context_path, image_name, project_name, model_name, version)
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


def _local_docker_image_exists(image_name: str) -> bool:
    """Whether an image tag is present in the local Docker daemon (no registry pull attempted)."""
    result = subprocess.run(["docker", "images", "-q", image_name], capture_output=True, text=True)
    return bool(result.stdout.strip())


def check_docker_image_exists(image_name: str) -> bool:
    docker_host = os.environ.get("DOCKER_HOST")
    logger.info(f"Checking if Docker image '{image_name}' exists with batch support (DOCKER_HOST={docker_host})")
    try:
        if not _local_docker_image_exists(image_name):
            logger.info(f"Docker image '{image_name}' does not exist")
            return False

        # Verify the image contains the batch predict template (old images may not have it)
        batch_template_path = "/opt/mlflow/batch_predict_template.py"
        check_cmd = ["docker", "run", "--rm", "--entrypoint", "test", image_name, "-f", batch_template_path]
        check = subprocess.run(check_cmd, capture_output=True)
        has_batch = check.returncode == 0
        if not has_batch:
            logger.info(f"Docker image '{image_name}' exists but lacks batch_predict_template.py, rebuild needed")
        else:
            logger.info(f"Docker image '{image_name}' exists with batch support")
        return has_batch
    except Exception as e:
        logger.warning(f"Failed to check Docker image existence: {e}")
        return False


def ensure_agent_base_image() -> bool:
    """
    Makes sure the shared `agent-base` image (langgraph/langchain/mlflow/fastapi/otel already
    installed, see infrastructure/docker/agent-base.Dockerfile) exists in the local Docker daemon,
    building it once if missing so agent Dockerfiles can `FROM` it
    (DockerfileTemplate.use_agent_base_image) and reuse uv's package cache instead of
    re-downloading the same heavy deps on every single agent deploy.

    Built lazily here rather than requiring a manual pre-build step, so agent deployment stays
    self-service even on a fresh environment — slower on the first agent deploy of the session
    only. `make k8s-agent-base-local` pre-warms it ahead of time to avoid paying that cost live.
    If the build itself fails (e.g. no network), we fall back to the plain python image instead
    of blocking the deployment on what is purely a speed optimization.
    """
    if _local_docker_image_exists(AGENT_BASE_IMAGE):
        return True

    dockerfile_path = os.path.join(PROJECT_DIR, "infrastructure", "docker", "agent-base.Dockerfile")
    if not os.path.isfile(dockerfile_path):
        logger.warning(f"Agent base Dockerfile not found at {dockerfile_path}, using the plain python image instead")
        return False

    logger.info(f"Agent base image '{AGENT_BASE_IMAGE}' not found, building it once (future deploys reuse it)...")
    tmp_root = os.path.join(PROJECT_DIR, "tmp")
    os.makedirs(tmp_root, exist_ok=True)
    build_context = tempfile.mkdtemp(dir=tmp_root, prefix="agent_base_build_")
    status = build_image_from_context(build_context, AGENT_BASE_IMAGE, dockerfile_path=dockerfile_path)
    if status == 0:
        logger.warning(
            f"Failed to build agent base image '{AGENT_BASE_IMAGE}', falling back to the plain "
            "python image for this build (slower, but the deployment will still succeed)"
        )
    return status == 1


def sanitize_name(project_name: str) -> str:
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", project_name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    return sanitized_name


def build_model_docker_image(
    registry: MLFlowModelRegistryAdapter, project_name: str, model_name: str, version: str, is_agent: bool = False
) -> int:
    """
    Generates and builds a Docker image for the specified model and version.

    Args:
        registry (MLFlowModelRegistryAdapter): The model registry adapter to use for downloading model artifacts.
        project_name: The name of the project.
        model_name (str): The name of the model.
        version (str): The version of the model.
        is_agent (bool): Whether this is an agent image (uses the pre-built agent-base image).

    Returns:
        str: The name of the built Docker image.

    """
    context_path: str = prepare_docker_context(registry, project_name, model_name, version)
    image_name: str = sanitize_name(f"{project_name}_{model_name}_{version}_ctr")
    build_status = build_docker_image_from_context_path(
        context_path,
        image_name,
        sanitize_name(project_name),
        sanitize_name(model_name),
        sanitize_name(version),
        is_agent=is_agent,
    )
    if build_status:
        # clean_build_context(context_path)
        pass
    return build_status
