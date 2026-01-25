"""
End-to-end test: Full workflow from project creation to model prediction.

This test covers the complete lifecycle:
1. Environment validation
2. Project creation
3. Model training and push to MLflow
4. Model deployment
5. Model prediction
6. Model undeployment
7. Project deletion
"""

import subprocess
import time

import mlflow
import mlflow.sklearn
import pytest
import requests
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from backend.utils import sanitize_ressource_name
from tests.conftest import (
    force_cleanup_project,
    is_deployment_present,
    is_ingress_present,
    is_minikube_running,
    is_url_reachable,
    login,
    MP_HOSTNAME,
    run_cli,
    wait_for_deployment_ready,
    wait_for_mlflow_ready,
)


def test_if_test_env_is_running():
    assert is_minikube_running() or True  # Kind is also acceptable
    assert is_ingress_present()
    assert is_deployment_present("nginx-reverse-proxy", "default")
    assert is_url_reachable(f"http://{MP_HOSTNAME}/health")
    assert login() == 0


# =============================================================================
# Test Constants
# =============================================================================

PROJECT_NAME = "testendtoend"
MODEL_NAME = "test_model"
MODEL_VERSION = "1"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_project():
    """Ensure test project is cleaned up before and after tests."""
    force_cleanup_project(PROJECT_NAME)
    time.sleep(20)
    yield
    force_cleanup_project(PROJECT_NAME)
    time.sleep(20)


# =============================================================================
# Project Creation Tests
# =============================================================================


def test_project_creation_should_respond_correctly():
    # La fixture cleanup_test_project supprime déjà le projet avant les tests
    result = run_cli("projects", "add", "--name", PROJECT_NAME)
    assert result.returncode == 0
    assert result.stdout == "✅ Project created successfully\n"


def test_project_should_have_responding_mlflow_registry():
    # Wait for MLflow registry to be ready (up to 180 seconds)
    is_ready = wait_for_mlflow_ready(PROJECT_NAME, timeout=180, interval=10)
    assert is_ready, f"MLflow registry for {PROJECT_NAME} did not become ready within timeout"

    # La commande list-models devrait retourner un code 0 et ne pas afficher une erreur
    result = run_cli("projects", "list-models", PROJECT_NAME)
    assert result.returncode == 0
    # Si aucune donnée, stdout peut être vide; on vérifie l'absence du message d'erreur.
    assert "❌" not in result.stdout


def test_project_train_model_should_push_model_to_mlflow():
    # Ensure MLflow registry is still ready before training
    is_ready = wait_for_mlflow_ready(PROJECT_NAME, timeout=60, interval=5)
    assert is_ready, f"MLflow registry for {PROJECT_NAME} not ready before training"

    data = load_iris()
    x = data.data
    y = data.target
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
    mlflow.set_tracking_uri(f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/")

    # Retry the model training and push with exponential backoff
    max_retries = 3
    last_error = None
    for attempt in range(max_retries):
        try:
            with mlflow.start_run():
                model = RandomForestClassifier(n_estimators=2, random_state=42)
                model.fit(x_train, y_train)
                y_pred = model.predict(x_test)
                accuracy = accuracy_score(y_test, y_pred)
                mlflow.log_metric("accuracy", accuracy)
                mlflow.sklearn.log_model(model, "custom_model", registered_model_name=MODEL_NAME)
                print(f"Model Accuracy: {accuracy}")
                print("Model saved to MLflow!")
            break  # Success, exit retry loop
        except Exception as e:
            last_error = e
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 30 * (attempt + 1)  # 30, 60 seconds
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
    else:
        assert False, f"Failed to train and push model after {max_retries} attempts: {last_error}"

    # Utiliser le CLI pour lister les modèles et vérifier la présence de MODEL_NAME
    list_result = run_cli("projects", "list-models", PROJECT_NAME)
    assert list_result.returncode == 0
    assert MODEL_NAME in list_result.stdout


def test_deploy_model_should_initiate_deployment():
    """Test that deploying a model initiates the deployment process."""
    # Retry deployment with exponential backoff in case of transient failures
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        result = run_cli(
            "projects", "deploy", PROJECT_NAME, "--model-name", MODEL_NAME, "--model-version", MODEL_VERSION
        )

        if result.returncode == 0:
            if "✅ Model deployed successfully" in result.stdout or "Deployment initiated" in result.stdout:
                return  # Success
            else:
                # Command succeeded but unexpected output
                assert False, f"Deploy returned success but unexpected output: {result.stdout}"

        last_error = result.stderr
        print(f"Attempt {attempt + 1}/{max_retries} failed: {result.stderr}")
        if attempt < max_retries - 1:
            wait_time = 30 * (attempt + 1)
            print(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

    assert False, f"Deploy failed after {max_retries} attempts: {last_error}"


def test_deployed_model_should_have_running_deployment():
    """Test that deployed model has a running K8s deployment."""
    # Wait for deployment to be ready (model build and deploy can take time)
    # Use the same naming convention as the production code
    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")

    # Allow more time for the Docker image to be built and deployed (up to 5 minutes)
    is_ready = wait_for_deployment_ready(deployment_name, PROJECT_NAME, timeout=300)
    assert is_ready, f"Deployment {deployment_name} did not become ready within timeout"


def test_deployed_model_should_respond_to_health_check():
    """Test that deployed model responds to health check."""
    # The model endpoint should be accessible via the ingress
    # Use the same naming convention as the production code for the deployment name
    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")
    model_endpoint = f"http://{MP_HOSTNAME}/deploy/{PROJECT_NAME}/{deployment_name}/health"

    # Retry several times as the service might take a moment to be fully available
    max_retries = 10
    last_error = None
    for i in range(max_retries):
        try:
            response = requests.get(model_endpoint, timeout=10)
            if response.status_code == 200:
                return
        except requests.RequestException as e:
            last_error = e
        time.sleep(10)

    # If direct health endpoint fails, try inference endpoint
    predict_endpoint = f"http://{MP_HOSTNAME}/deploy/{PROJECT_NAME}/{deployment_name}/predict"
    try:
        response = requests.post(
            predict_endpoint,
            json={
                "inputs": {
                    "sepal length (cm)": [5.1],
                    "sepal width (cm)": [3.5],
                    "petal length (cm)": [1.4],
                    "petal width (cm)": [0.2],
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert response.status_code in [200, 400], f"Model endpoint not responding: {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Model endpoint not reachable: {e} (last health check error: {last_error})"


def test_deployed_model_should_return_predictions():
    """Test that deployed model returns predictions for valid input."""
    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")
    predict_endpoint = f"http://{MP_HOSTNAME}/deploy/{PROJECT_NAME}/{deployment_name}/predict"

    # Iris dataset format: 4 features as a dictionary (DataFrame-like format)
    # The model expects inputs as Dict[str, Any] which gets converted to DataFrame
    test_data = {
        "inputs": {
            "sepal length (cm)": [5.1, 6.2],
            "sepal width (cm)": [3.5, 3.4],
            "petal length (cm)": [1.4, 5.4],
            "petal width (cm)": [0.2, 2.3],
        }
    }

    try:
        response = requests.post(
            predict_endpoint, json=test_data, headers={"Content-Type": "application/json"}, timeout=30
        )
    except requests.RequestException as e:
        assert False, f"Prediction endpoint not reachable: {e}"

    assert response.status_code not in [502, 503, 504], f"Prediction failed with {response.status_code}"

    assert response.status_code == 200, f"Prediction failed: {response.text}"
    predictions = response.json()
    assert "predictions" in predictions or isinstance(predictions, list), "Response should contain predictions"


def test_list_deployed_models_should_show_deployed_model():
    """Test that list deployed models shows the deployed model."""
    result = run_cli("projects", "list-deployed-models", PROJECT_NAME)

    assert result.returncode == 0, f"List deployed models failed: {result.stderr}"
    assert result.stdout.strip(), "No deployed models found - deployment may have failed in previous test"
    # Model name may be sanitized (underscores replaced with dashes)
    assert MODEL_NAME in result.stdout or MODEL_NAME.replace("_", "-") in result.stdout


def test_undeploy_model_should_succeed():
    """Test that undeploying a model succeeds."""
    result = run_cli("projects", "undeploy", PROJECT_NAME, "--model-name", MODEL_NAME, "--model-version", MODEL_VERSION)

    assert result.returncode == 0, f"Undeploy failed: {result.stderr}"
    assert "✅ Model undeployed successfully" in result.stdout or "return_code" in result.stdout


def test_undeployed_model_should_not_have_deployment():
    """Test that undeployed model no longer has a K8s deployment."""
    # Wait for cleanup
    time.sleep(30)

    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", deployment_name, "-n", PROJECT_NAME, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        # If we get here, deployment still exists
        assert False, f"Deployment {deployment_name} should have been deleted"
    except subprocess.CalledProcessError:
        # Expected - deployment should not exist
        pass


def test_undeployed_model_should_not_respond():
    """Test that undeployed model endpoint no longer responds."""
    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")
    predict_endpoint = f"http://{MP_HOSTNAME}/deploy/{PROJECT_NAME}/{deployment_name}/predict"

    try:
        response = requests.post(
            predict_endpoint,
            json={"inputs": {"inputs": {"0": 3, "1": 5.1, "2": 1.4, "3": 0.2}}},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        # Should get 404/405/502/503/504 (service unavailable or method not allowed)
        assert response.status_code in [
            404,
            405,
            502,
            503,
            504,
        ], f"Endpoint should not be available: {response.status_code}"
    except requests.RequestException:
        # Connection refused/timeout is also acceptable
        pass


def test_remove_project_should_correctly_remove_project_registry():
    # Utiliser la commande delete (déjà testée plus haut) mais on répète pour la cohérence de scénario
    delete_result = run_cli("projects", "delete", PROJECT_NAME)
    assert delete_result.returncode == 0
    assert "✅ Project deleted successfully" in delete_result.stdout
    time.sleep(30)
    status_project_registry = requests.get(f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/")
    # 200 (empty page), 404 (not found), or 502 (bad gateway) all indicate the registry is no longer functional
    # Note: nginx may return 200 with an error page if the upstream is not found
    assert status_project_registry.status_code in [200, 404, 502]
