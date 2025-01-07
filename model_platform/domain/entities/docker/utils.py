from docker.errors import DockerException
from loguru import logger


def _display_docker_build_logs(build_logs):
    for chunk in build_logs:
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                logger.info(line)


def build_image_from_context(context_dir: str, image_name: str) -> int:
    import docker

    try:
        client = docker.from_env()
    except DockerException as e:
        logger.error(f"Could not connect to Docker daemon: {e}. Have you set DOCKER_HOST environment variable?")
        return 1

    # In Docker < 19, `docker build` doesn't support the `--platform` option
    is_platform_supported = int(client.version()["Version"].split(".")[0]) >= 19
    # Enforcing the AMD64 architecture build for Apple M1 users
    platform_option = "linux/amd64" if is_platform_supported else ""
    try:
        _, build_logs = client.images.build(path=context_dir, tag=image_name, platform=platform_option)
        logger.info(f"Image '{image_name}' built successfully.")
        return 0
    except docker.errors.BuildError as e:
        raise RuntimeError(f"Docker build failed: {e}")
