"""
Shared fixtures and utilities for all tests.
"""

import os
import subprocess
import time

import pytest


# =============================================================================
# Constants
# =============================================================================

MP_HOSTNAME = os.environ.get("MP_HOSTNAME", "model-platform.com")

DEFAULT_TEST_USER = {
    "username": os.environ.get("MP_TEST_USERNAME", "alice@example.com"),
    "password": os.environ.get("MP_TEST_PASSWORD", "pass!"),
}

TEST_PROJECT_NAMES = [
    "integration-test-project",
    "integration-test-model",
    "test",
]


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
# Cleanup Helpers
# =============================================================================


def cleanup_project(project_name: str) -> None:
    """Delete a project via CLI and kubectl (to ensure complete cleanup)."""
    # Try CLI deletion first (this cleans DB + namespace)
    run_cli("projects", "delete", project_name)

    # Delete namespace and wait for it to be fully removed
    subprocess.run(
        ["kubectl", "delete", "namespace", project_name, "--ignore-not-found"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Poll until namespace is actually gone (handles edge cases)
    deadline = time.time() + 120
    while time.time() < deadline:
        result = subprocess.run(
            ["kubectl", "get", "namespace", project_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return
        time.sleep(5)
    print(f"[WARNING] Namespace {project_name} still exists after 120s cleanup timeout")


def cleanup_test_namespaces(project_names: list[str] | None = None) -> None:
    """Cleanup all test namespaces."""
    if project_names is None:
        project_names = TEST_PROJECT_NAMES

    for project_name in project_names:
        cleanup_project(project_name)


# =============================================================================
# K8s Check Helpers
# =============================================================================


def is_kubectl_available() -> bool:
    """Check if kubectl is available and configured."""
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
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


# =============================================================================
# Pytest Markers Configuration
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests requiring full infrastructure")


# =============================================================================
# Shared Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def mp_hostname():
    """Get the Model Platform hostname."""
    return MP_HOSTNAME
