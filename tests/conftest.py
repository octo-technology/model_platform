"""
Shared fixtures and utilities for all tests (integration and end-to-end).

This module provides:
- Common helper functions for K8s, CLI, and HTTP operations
- Shared fixtures for login, cleanup, and environment checks
- Utility functions for deployment and service management
"""

import json
import os
import subprocess
import time

import pytest
import requests
from loguru import logger


# =============================================================================
# Constants
# =============================================================================

MP_HOSTNAME = os.environ.get("MP_HOSTNAME", "model-platform.com")

TEST_PROJECT_NAMES = [
    "integration-test-project",
    "integration-test-model",
    "test",
]

DEFAULT_TEST_USER = {
    "username": os.environ.get("MP_TEST_USERNAME", "alice@example.com"),
    "password": os.environ.get("MP_TEST_PASSWORD", "pass!"),
}


# =============================================================================
# CLI Helpers
# =============================================================================


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Helper to run CLI commands."""
    return subprocess.run(["mp", *args], capture_output=True, text=True)


def login(username: str | None = None, password: str | None = None) -> int:
    """Login to the platform via CLI."""
    username = username or DEFAULT_TEST_USER["username"]
    password = password or DEFAULT_TEST_USER["password"]
    result = run_cli("login", "--username", username, "--password", password)
    return result.returncode


# =============================================================================
# Environment Check Helpers
# =============================================================================


def is_kubectl_available() -> bool:
    """Check if kubectl is available and configured."""
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_kind_running() -> bool:
    """Check if Kind cluster is running."""
    try:
        result = subprocess.run(
            ["kind", "get", "clusters"],
            capture_output=True,
            text=True,
            check=True,
        )
        return "model-platform" in result.stdout or len(result.stdout.strip()) > 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def is_minikube_running() -> bool:
    """Check if Minikube is running."""
    try:
        result = subprocess.run(
            ["minikube", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "Running" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_cluster_available() -> bool:
    """Check if any K8s cluster (Kind or Minikube) is available."""
    return is_kubectl_available() and (is_kind_running() or is_minikube_running())


# =============================================================================
# K8s Resource Helpers
# =============================================================================


def namespace_exists(namespace: str) -> bool:
    """Check if a namespace exists in K8s."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "namespace", namespace],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def delete_namespace(namespace: str, wait: bool = False, timeout: int = 60) -> bool:
    """
    Delete a namespace from K8s.

    Args:
        namespace: The namespace to delete
        wait: Whether to wait for the namespace to be fully deleted
        timeout: Maximum time to wait for deletion (in seconds)

    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        subprocess.run(
            ["kubectl", "delete", "namespace", namespace, "--ignore-not-found"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        if wait:
            start_time = time.time()
            while time.time() - start_time < timeout:
                result = subprocess.run(
                    ["kubectl", "get", "namespace", namespace],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return True
                time.sleep(5)
            return False

        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def get_namespace(namespace: str) -> dict | None:
    """Get namespace info from K8s."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "namespace", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def get_deployment(deployment_name: str, namespace: str) -> dict | None:
    """Get deployment info from K8s."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", deployment_name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def get_service(service_name: str, namespace: str) -> dict | None:
    """Get service info from K8s."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "service", service_name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def is_deployment_present(deployment_name: str, namespace: str = "default") -> bool:
    """Check if a deployment exists."""
    return get_deployment(deployment_name, namespace) is not None


def is_ingress_present(ingress_name: str = "registry-ingress", namespace: str = "default") -> bool:
    """Check if an ingress exists."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "ingress", ingress_name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(json.loads(result.stdout))
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return False


def wait_for_deployment_ready(deployment_name: str, namespace: str, timeout: int = 120) -> bool:
    """Wait for deployment to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        deployment = get_deployment(deployment_name, namespace)
        if deployment:
            status = deployment.get("status", {})
            ready_replicas = status.get("readyReplicas", 0)
            replicas = status.get("replicas", 1)
            if ready_replicas >= replicas and ready_replicas > 0:
                return True
        time.sleep(5)
    return False


# =============================================================================
# HTTP Helpers
# =============================================================================


def is_url_reachable(url: str, timeout: int = 5) -> bool:
    """Check if a URL is reachable."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        logger.error(f"Failed to reach URL: {url}")
        return False


def send_get_request(url: str, params: dict = None, headers: dict = None, timeout: int = 5) -> dict:
    """Send a GET request and return response info."""
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        return {"status_code": response.status_code, "response": response.text}
    except requests.RequestException as e:
        return {"error": str(e)}


def send_post_request(url: str, data: dict, headers: dict = None, timeout: int = 5) -> dict:
    """Send a POST request and return response info."""
    try:
        if headers is None:
            headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers, timeout=timeout)
        return {"status_code": response.status_code, "response": response.text}
    except requests.RequestException as e:
        return {"error": str(e)}


def is_mlflow_reachable(project_name: str, timeout: int = 5) -> bool:
    """Check if MLflow registry is reachable for the given project."""
    url = f"http://{MP_HOSTNAME}/registry/{project_name}/health"
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def wait_for_mlflow_ready(project_name: str, timeout: int = 120, interval: int = 5) -> bool:
    """Wait for MLflow registry to become ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_mlflow_reachable(project_name):
            return True
        time.sleep(interval)
    return False


# =============================================================================
# Cleanup Helpers
# =============================================================================


def cleanup_via_cli(project_name: str) -> bool:
    """
    Delete a project via the CLI (preferred method as it handles all related resources).

    Args:
        project_name: The project name to delete

    Returns:
        True if deletion was attempted, False if CLI is not available
    """
    try:
        subprocess.run(
            ["mp", "projects", "delete", project_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def force_cleanup_project(project_name: str) -> None:
    """
    Force cleanup a project using both CLI and direct K8s commands.

    This ensures cleanup even if the CLI fails.

    Args:
        project_name: The project name to cleanup
    """
    cleanup_via_cli(project_name)
    if namespace_exists(project_name):
        delete_namespace(project_name, wait=False)


def cleanup_test_namespaces(project_names: list[str] | None = None) -> None:
    """
    Cleanup all test namespaces.

    Args:
        project_names: List of project names to cleanup. Defaults to TEST_PROJECT_NAMES.
    """
    if project_names is None:
        project_names = TEST_PROJECT_NAMES

    for project_name in project_names:
        if namespace_exists(project_name):
            print(f"Cleaning up stale test namespace: {project_name}")
            delete_namespace(project_name, wait=False)


# =============================================================================
# Pytest Markers Configuration
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "destructive: marks tests that modify cluster state significantly")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests requiring full infrastructure")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


# =============================================================================
# Shared Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def mp_hostname():
    """Get the Model Platform hostname."""
    return MP_HOSTNAME


@pytest.fixture(scope="session")
def test_user_credentials():
    """Get test user credentials."""
    return DEFAULT_TEST_USER


@pytest.fixture(scope="session")
def logged_in_session():
    """Ensure user is logged in for the session."""
    result = login()
    if result != 0:
        pytest.skip("Cannot login to platform - skipping tests")
    return True


@pytest.fixture
def ensure_namespace_cleanup():
    """
    Fixture that ensures a namespace is cleaned up after the test.

    Usage:
        def test_something(ensure_namespace_cleanup):
            namespace = "my-test-namespace"
            ensure_namespace_cleanup(namespace)
            # ... test code ...

    The namespace will be deleted even if the test fails.
    """
    namespaces_to_cleanup = []

    def _register_namespace(namespace: str):
        namespaces_to_cleanup.append(namespace)

    yield _register_namespace

    for namespace in namespaces_to_cleanup:
        force_cleanup_project(namespace)
