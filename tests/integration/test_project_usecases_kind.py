"""
Integration tests for project use cases using Kind (lightweight K8s).

These tests verify the core project management use cases:
- Project creation
- Project listing
- Project deletion
- MLflow registry connectivity

Run with: pytest tests/integration/test_project_usecases_kind.py -v
Requires: Kind cluster running with basic infrastructure
"""

import json
import subprocess
import time

import pytest

from tests.integration.conftest import (
    force_cleanup_project,
    is_kind_running,
    is_kubectl_available,
    run_cli,
)


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


def wait_for_deployment_ready(deployment_name: str, namespace: str, timeout: int = 120) -> bool:
    """Wait for deployment to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        deployment = get_deployment(deployment_name, namespace)
        if deployment:
            status = deployment.get("status", {})
            ready_replicas = status.get("readyReplicas", 0)
            replicas = status.get("replicas", 1)
            if ready_replicas >= replicas:
                return True
        time.sleep(5)
    return False



# Skip all tests if Kind is not available
pytestmark = pytest.mark.skipif(
    not is_kind_running() and not is_kubectl_available(),
    reason="Kind cluster or kubectl not available"
)


PROJECT_NAME = "integration-test-project"


@pytest.fixture(scope="module")
def login_fixture():
    """Login to the platform before running tests."""
    result = run_cli("login", "--username", "alice@example.com", "--password", "pass!")
    if result.returncode != 0:
        pytest.skip("Cannot login to platform - skipping integration tests")
    return True


@pytest.fixture(scope="module", autouse=True)
def cleanup_project():
    """
    Cleanup project before and after tests.

    This fixture ensures cleanup happens even if tests fail:
    - Before tests: Remove any leftover resources from previous runs
    - After tests: Always cleanup, using both CLI and direct K8s commands
    """
    # Cleanup before tests start (in case previous run failed)
    force_cleanup_project(PROJECT_NAME)
    time.sleep(5)

    try:
        yield
    finally:
        # Always cleanup after tests, even if they fail
        force_cleanup_project(PROJECT_NAME)
        # Wait for namespace to be deleted
        time.sleep(10)


class TestProjectCreation:
    """Tests for project creation use case."""

    def test_create_project_should_succeed(self, login_fixture):
        """Test that project creation succeeds and returns correct message."""
        result = run_cli("projects", "add", "--name", PROJECT_NAME)

        assert result.returncode == 0, f"Project creation failed: {result.stderr}"
        assert "✅ Project created successfully" in result.stdout

    def test_create_project_should_create_namespace(self, login_fixture):
        """Test that project creation creates the K8s namespace."""
        # Wait for namespace to be created
        time.sleep(10)

        namespace = get_namespace(PROJECT_NAME)
        assert namespace is not None, f"Namespace {PROJECT_NAME} was not created"

    def test_create_project_should_create_mlflow_deployment(self, login_fixture):
        """Test that project creation creates MLflow deployment."""
        # Wait for deployment
        time.sleep(20)

        deployment = get_deployment(PROJECT_NAME, PROJECT_NAME)
        assert deployment is not None, f"MLflow deployment was not created for {PROJECT_NAME}"

    def test_create_project_should_create_mlflow_service(self, login_fixture):
        """Test that project creation creates MLflow service."""
        service = get_service(PROJECT_NAME, PROJECT_NAME)
        assert service is not None, f"MLflow service was not created for {PROJECT_NAME}"


class TestProjectMlflowRegistry:
    """Tests for MLflow registry functionality."""

    def test_mlflow_registry_should_be_accessible(self, login_fixture):
        """Test that MLflow registry responds to requests."""
        # Wait for MLflow to be ready
        deployment_ready = wait_for_deployment_ready(
            PROJECT_NAME,
            PROJECT_NAME,
            timeout=10
        )
        assert deployment_ready, "MLflow deployment did not become ready in time"

    def test_list_models_should_succeed(self, login_fixture):
        """Test that listing models works even when empty."""
        # Give some time for the registry to be fully operational
        time.sleep(5)

        result = run_cli("projects", "list-models", PROJECT_NAME)

        assert result.returncode == 0, f"List models failed: {result.stderr}"
        assert "❌" not in result.stdout, "Error occurred while listing models"


class TestProjectListing:
    """Tests for project listing use case."""

    def test_list_projects_should_include_created_project(self, login_fixture):
        """Test that created project appears in project list."""
        result = run_cli("projects", "list")

        assert result.returncode == 0, f"List projects failed: {result.stderr}"
        # Project should be in the list (might be in JSON format or table)
        assert PROJECT_NAME in result.stdout or "integration-test" in result.stdout


class TestProjectDeletion:
    """Tests for project deletion use case."""

    def test_delete_project_should_succeed(self, login_fixture):
        """Test that project deletion succeeds."""
        result = run_cli("projects", "delete", PROJECT_NAME)

        assert result.returncode == 0, f"Project deletion failed: {result.stderr}"
        assert "✅ Project deleted successfully" in result.stdout

    def test_delete_project_should_remove_namespace(self, login_fixture):
        """Test that project deletion removes the K8s namespace."""
        # Wait for namespace deletion
        time.sleep(60)

        namespace = get_namespace(PROJECT_NAME)
        assert namespace is None, f"Namespace {PROJECT_NAME} was not deleted"

    def test_delete_project_should_remove_mlflow_deployment(self, login_fixture):
        """Test that project deletion removes MLflow deployment."""
        deployment = get_deployment(PROJECT_NAME, PROJECT_NAME)
        assert deployment is None, "MLflow deployment was not removed"

    def test_deleted_project_should_not_appear_in_list(self, login_fixture):
        """Test that deleted project no longer appears in project list."""
        result = run_cli("projects", "list")

        # Project should not be in the list
        assert PROJECT_NAME not in result.stdout
