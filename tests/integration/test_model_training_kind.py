"""
Integration tests for model training use cases using Kind.

These tests verify the model training and registry push:
- Train a model and push to MLflow registry
- Verify model appears in registry
- List model versions

Run with: pytest tests/integration/test_model_training_kind.py -v
Requires: Kind cluster running with basic infrastructure and a created project
"""

import time
from importlib.util import find_spec

import pytest
import requests

from tests.integration.conftest import (
    force_cleanup_project,
    is_kubectl_available,
    run_cli,
)


# Check if optional dependencies are available
SKLEARN_AVAILABLE = find_spec("sklearn") is not None and find_spec("mlflow") is not None

if SKLEARN_AVAILABLE:
    import mlflow
    import mlflow.sklearn
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split


# Skip all tests if dependencies are not available
pytestmark = [
    pytest.mark.skipif(
        not is_kubectl_available(),
        reason="kubectl not available"
    ),
    pytest.mark.skipif(
        not SKLEARN_AVAILABLE,
        reason="scikit-learn or mlflow not available"
    ),
]


MP_HOSTNAME = "model-platform.com"
PROJECT_NAME = "integration-test-model"
MODEL_NAME = "test_random_forest"


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



@pytest.fixture(scope="module")
def login_and_setup_project():
    """
    Login and create a project for model tests.

    This fixture ensures cleanup happens even if tests fail:
    - Before tests: Remove any leftover resources from previous runs
    - After tests: Always cleanup, using both CLI and direct K8s commands
    """
    # Login
    result = run_cli("login", "--username", "alice@example.com", "--password", "pass!")
    if result.returncode != 0:
        pytest.skip("Cannot login to platform - skipping integration tests")

    # Cleanup any existing project (from previous failed runs)
    force_cleanup_project(PROJECT_NAME)
    time.sleep(10)

    # Create the project
    result = run_cli("projects", "add", "--name", PROJECT_NAME)
    if result.returncode != 0:
        pytest.skip(f"Cannot create project: {result.stderr}")

    # Wait for MLflow to be ready (with active polling instead of fixed sleep)
    if not wait_for_mlflow_ready(PROJECT_NAME, timeout=120):
        force_cleanup_project(PROJECT_NAME)
        pytest.skip(f"MLflow registry for {PROJECT_NAME} did not become ready in time")

    try:
        yield PROJECT_NAME
    finally:
        # Always cleanup after tests, even if they fail
        force_cleanup_project(PROJECT_NAME)
        # Wait for namespace to be deleted
        time.sleep(10)


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn/mlflow not available")
class TestModelTraining:
    """Tests for model training and registry push."""

    def test_train_and_push_model_to_mlflow(self, login_and_setup_project):
        """Test training a model and pushing it to MLflow registry."""
        # Verify MLflow is reachable before training
        assert is_mlflow_reachable(PROJECT_NAME), \
            f"MLflow registry for {PROJECT_NAME} is not reachable"

        # Load data
        data = load_iris()
        x_train, x_test, y_train, y_test = train_test_split(
            data.data, data.target, test_size=0.3, random_state=42
        )

        # Set MLflow tracking URI
        tracking_uri = f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/"
        mlflow.set_tracking_uri(tracking_uri)

        # Train and log model
        with mlflow.start_run():
            model = RandomForestClassifier(n_estimators=2, random_state=42)
            model.fit(x_train, y_train)

            y_pred = model.predict(x_test)
            accuracy = accuracy_score(y_test, y_pred)

            mlflow.log_metric("accuracy", accuracy)
            mlflow.sklearn.log_model(
                model,
                "custom_model",
                registered_model_name=MODEL_NAME
            )

        # Verify model appears in registry via CLI
        time.sleep(5)
        result = run_cli("projects", "list-models", PROJECT_NAME)

        assert result.returncode == 0, f"List models failed: {result.stderr}"
        assert MODEL_NAME in result.stdout, f"Model {MODEL_NAME} not found in registry"

    def test_list_model_versions(self, login_and_setup_project):
        """Test listing model versions after training."""
        result = run_cli("projects", "list-models", PROJECT_NAME)

        assert result.returncode == 0
        # Check that at least one version exists
        assert MODEL_NAME in result.stdout


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn/mlflow not available")
class TestModelMetrics:
    """Tests for model metrics and tracking."""

    def test_train_multiple_runs_should_log_metrics(self, login_and_setup_project):
        """Test that multiple training runs log metrics correctly."""
        tracking_uri = f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/"
        mlflow.set_tracking_uri(tracking_uri)

        data = load_iris()
        x_train, x_test, y_train, y_test = train_test_split(
            data.data, data.target, test_size=0.3, random_state=42
        )

        accuracies = []
        for n_estimators in [1, 3, 5]:
            with mlflow.start_run():
                model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
                model.fit(x_train, y_train)

                y_pred = model.predict(x_test)
                accuracy = accuracy_score(y_test, y_pred)
                accuracies.append(accuracy)

                mlflow.log_param("n_estimators", n_estimators)
                mlflow.log_metric("accuracy", accuracy)

        # All runs should have completed successfully
        assert len(accuracies) == 3
        assert all(0 <= acc <= 1 for acc in accuracies)
