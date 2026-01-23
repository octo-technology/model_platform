"""
Shared fixtures and cleanup logic for integration tests.

This module provides:
- Automatic cleanup of stale test resources
- Session-level cleanup hooks
- Utility functions for K8s resource management
- Common helper functions for all integration tests
"""

import subprocess
import time
from typing import Generator

import pytest


# List of test project names that might be created by tests
TEST_PROJECT_NAMES = [
    "integration-test-project",
    "integration-test-model",
]


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


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Helper to run CLI commands."""
    return subprocess.run(["mp", *args], capture_output=True, text=True)


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
                    # Namespace no longer exists
                    return True
                time.sleep(5)
            return False

        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


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
            timeout=10,
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
    # Try CLI first (handles DB cleanup, etc.)
    cleanup_via_cli(project_name)

    # Then force namespace deletion via kubectl
    if namespace_exists(project_name):
        delete_namespace(project_name, wait=False)


@pytest.fixture(scope="session", autouse=True)
def cleanup_stale_test_resources() -> Generator[None, None, None]:
    """
    Session-level fixture that cleans up stale test resources.

    This runs:
    - Before all tests: Cleanup any leftover resources from previous runs
    - After all tests: Cleanup resources created during this run
    """
    # Cleanup before tests start
    print("\n[Integration Tests] Cleaning up stale test resources before test run...")
    cleanup_test_namespaces()

    # Wait a bit for namespaces to start terminating
    time.sleep(5)

    yield

    # Cleanup after all tests complete
    print("\n[Integration Tests] Cleaning up test resources after test run...")
    cleanup_test_namespaces()


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

    # Cleanup registered namespaces
    for namespace in namespaces_to_cleanup:
        force_cleanup_project(namespace)
