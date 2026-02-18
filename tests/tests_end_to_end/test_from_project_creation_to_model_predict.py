"""
End-to-end test: Full workflow from project creation to model prediction.

This test covers the complete lifecycle:
1. Project creation
2. Model training and push to MLflow
3. Model deployment
4. Model prediction
5. Model undeployment
6. Project deletion
"""

import random
import string
import subprocess
import time
import os

import mlflow
import mlflow.sklearn
import pytest
import requests
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.utils import sanitize_ressource_name
from tests.conftest import cleanup_project, login, MP_HOSTNAME, run_cli

# Use random suffix to avoid conflicts with previous test runs (db dropper jobs, etc.)
PROJECT_SUFFIX = "".join(random.choices(string.ascii_lowercase, k=6))
PROJECT_NAME = f"e2e{PROJECT_SUFFIX}"
MODEL_NAME = "test_model"
MODEL_VERSION = "1"


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Clean up project before and after tests."""
    # Setup: Login and configure docker env for minikube
    print("[DEBUG] Setting up e2e test environment")

    # Check minikube status first
    try:
        result = subprocess.run(["minikube", "status"], capture_output=True, text=True, timeout=30)
        print(f"[DEBUG] minikube status exit code: {result.returncode}")
        print(f"[DEBUG] minikube status output:\n{result.stdout}")
        if result.stderr:
            print(f"[DEBUG] minikube status stderr:\n{result.stderr}")
    except Exception as exc:
        print(f"[DEBUG] Error checking minikube status: {exc}")

    _setup_minikube_docker_env()
    assert login() == 0, "Login failed"

    yield

    # Teardown: cleanup
    cleanup_project(PROJECT_NAME)


def test_health_endpoint_responds():
    """Test that the platform health endpoint responds."""
    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://{MP_HOSTNAME}/health"],
        capture_output=True,
        text=True,
    )
    assert result.stdout == "200", f"Health endpoint did not respond with 200: {result.stdout}"


def test_project_creation():
    """Test project creation."""
    result = run_cli("projects", "add", "--name", PROJECT_NAME)
    assert result.returncode == 0, f"Project creation failed: {result.stderr}"
    assert "✅ Project created successfully" in result.stdout


def test_mlflow_registry_responds():
    """Test that MLflow registry responds after project creation."""
    # Wait for MLflow to be ready
    time.sleep(60)

    result = subprocess.run(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/#/models",
        ],
        capture_output=True,
        text=True,
    )
    assert result.stdout == "200", f"MLflow registry did not respond with 200: {result.stdout}"
    global _mlflow_ready
    _mlflow_ready = True


# Flag to track if MLflow is ready
_mlflow_ready = False


def _skip_if_mlflow_not_ready():
    if not _mlflow_ready:
        pytest.skip("MLflow registry not ready - skipping dependent test")


# --- Debug helpers to surface CI failures ---


def _setup_minikube_docker_env():
    """Ensure we're using minikube's docker daemon for image builds."""
    print("[DEBUG] Configuring minikube docker environment...")
    try:
        # Get minikube docker env
        result = subprocess.run(
            ["minikube", "docker-env", "--shell", "bash"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(f"[DEBUG] minikube docker-env exit code: {result.returncode}")
        if result.returncode == 0:
            print(f"[DEBUG] minikube docker-env output:\n{result.stdout}")
            # Parse the env vars from minikube docker-env output
            env_lines = [line.strip() for line in result.stdout.split("\n") if line.startswith("export ")]
            for line in env_lines:
                if "=" in line:
                    # Extract VAR=value from "export VAR=value"
                    var_assignment = line.replace("export ", "", 1)
                    if "=" in var_assignment:
                        key, value = var_assignment.split("=", 1)
                        # Remove quotes from value if present
                        value = value.strip("\"'")
                        os.environ[key] = value
                        print(f"[DEBUG] Set {key}={value}")
            print("[DEBUG] Minikube docker environment configured successfully")

            # Verify the configuration worked
            docker_host = os.environ.get("DOCKER_HOST", "not set")
            print(f"[DEBUG] Current DOCKER_HOST: {docker_host}")
        else:
            print(f"[DEBUG] Failed to get minikube docker-env: {result.stderr}")
            print(f"[DEBUG] minikube docker-env stdout: {result.stdout}")
    except Exception as exc:
        print(f"[DEBUG] Error setting up minikube docker env: {exc}")


def _run_debug_cmd(label, cmd):
    print(f"[DEBUG] {label}: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        print(f"[DEBUG] {label} exit={result.returncode}")
        if result.stdout:
            print(f"[DEBUG] {label} stdout:\n{result.stdout}")
        if result.stderr:
            print(f"[DEBUG] {label} stderr:\n{result.stderr}")
    except Exception as exc:  # noqa: BLE001 - debug path only
        print(f"[DEBUG] {label} error: {exc}")


def _first_pod_name(namespace):
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "--no-headers"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().splitlines()[0].split()[0]
    return None


def _dump_deployment_debug_info(deployment_name):
    print(f"[DEBUG] Dumping state for deployment {deployment_name} in namespace {PROJECT_NAME}")
    _run_debug_cmd("kubectl get pods", ["kubectl", "get", "pods", "-n", PROJECT_NAME, "-o", "wide"])
    _run_debug_cmd(
        "kubectl get deployment",
        ["kubectl", "get", "deployment", deployment_name, "-n", PROJECT_NAME, "-o", "yaml"],
    )
    _run_debug_cmd("kubectl get svc", ["kubectl", "get", "svc", "-n", PROJECT_NAME])
    _run_debug_cmd(
        "kubectl get events",
        ["kubectl", "get", "events", "-n", PROJECT_NAME, "--sort-by=.metadata.creationTimestamp"],
    )

    # Check all pods for this specific deployment (not just first pod in namespace)
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", PROJECT_NAME, "-l", f"app={deployment_name}", "--no-headers"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode == 0 and result.stdout.strip():
        pod_lines = result.stdout.strip().splitlines()
        for line in pod_lines:
            pod_name = line.split()[0]
            print(f"[DEBUG] Checking logs for pod: {pod_name}")
            _run_debug_cmd(
                f"kubectl describe pod {pod_name}", ["kubectl", "describe", "pod", pod_name, "-n", PROJECT_NAME]
            )
            _run_debug_cmd(
                f"kubectl logs current {pod_name}", ["kubectl", "logs", pod_name, "-n", PROJECT_NAME, "--tail=100"]
            )
            _run_debug_cmd(
                f"kubectl logs previous {pod_name}",
                ["kubectl", "logs", pod_name, "-n", PROJECT_NAME, "--previous", "--tail=100"],
            )
    else:
        # Fallback to first pod in namespace
        pod_name = _first_pod_name(PROJECT_NAME)
        if pod_name:
            _run_debug_cmd("kubectl describe pod", ["kubectl", "describe", "pod", pod_name, "-n", PROJECT_NAME])
            _run_debug_cmd("kubectl logs current", ["kubectl", "logs", pod_name, "-n", PROJECT_NAME])
            _run_debug_cmd("kubectl logs previous", ["kubectl", "logs", pod_name, "-n", PROJECT_NAME, "--previous"])

    # Also check available images in minikube
    _run_debug_cmd("minikube image ls", ["minikube", "image", "ls"])


def _dump_registry_status():
    registry_url = f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/"
    _run_debug_cmd("curl registry index", ["curl", "-v", "--max-time", "20", registry_url])


def test_train_and_push_model_to_mlflow():
    """Test model training and push to MLflow."""
    time.sleep(120)
    _skip_if_mlflow_not_ready()
    # Verify MLflow API is operational before pushing
    api_url = f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/api/2.0/mlflow/experiments/search"
    response = requests.post(api_url, json={"max_results": 1}, timeout=10)
    assert response.status_code == 200, f"MLflow API not ready: {response.status_code}"

    data = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(data.data, data.target, test_size=0.3, random_state=42)

    mlflow.set_tracking_uri(f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/")

    with mlflow.start_run():
        model = RandomForestClassifier(n_estimators=2, random_state=42)
        model.fit(x_train, y_train)
        mlflow.sklearn.log_model(model, name="custom_model", registered_model_name=MODEL_NAME)

    # Verify model is registered
    time.sleep(60)
    result = run_cli("projects", "list-models", PROJECT_NAME)
    assert result.returncode == 0, f"list-models failed: {result.stderr}"
    assert MODEL_NAME in result.stdout, f"Model {MODEL_NAME} not found in: {result.stdout}"


def test_deploy_model():
    """Test model deployment."""
    _skip_if_mlflow_not_ready()

    # Verify Docker environment is still configured for minikube
    docker_host = os.environ.get("DOCKER_HOST", "not set")
    print(f"[DEBUG] Deploy test - Current DOCKER_HOST: {docker_host}")

    result = run_cli("projects", "deploy", PROJECT_NAME, "--model-name", MODEL_NAME, "--model-version", MODEL_VERSION)

    # Check if image exists in minikube after deployment
    expected_image_name = (
        f"{PROJECT_NAME.lower().replace('_', '-')}-{MODEL_NAME.lower().replace('_', '-')}-{MODEL_VERSION}-ctr:latest"
    )
    print(f"[DEBUG] Expected image name: {expected_image_name}")
    _run_debug_cmd("minikube image ls", ["minikube", "image", "ls"])

    # Also check docker images to see what's available
    _run_debug_cmd("docker images", ["docker", "images"])

    assert result.returncode == 0, f"Deploy failed: {result.stderr}"


def test_deployed_model_health_check():
    """Test that deployed model responds to health check."""
    _skip_if_mlflow_not_ready()
    time.sleep(180)
    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")

    # Check pod status first for debugging
    print(f"[DEBUG] Checking pod status for deployment {deployment_name}")
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", PROJECT_NAME, "-l", f"app={deployment_name}", "--no-headers"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode == 0 and result.stdout.strip():
        pod_lines = result.stdout.strip().splitlines()
        for line in pod_lines:
            parts = line.split()
            if len(parts) >= 3:
                pod_name, ready, status = parts[0], parts[1], parts[2]
                print(f"[DEBUG] Pod {pod_name}: ready={ready}, status={status}")
                if status not in ["Running", "Pending"]:
                    print(f"[DEBUG] Pod is in unexpected state: {status}, checking logs...")
                    _run_debug_cmd(
                        f"kubectl logs {pod_name}", ["kubectl", "logs", pod_name, "-n", PROJECT_NAME, "--tail=50"]
                    )

    health_url = f"http://{MP_HOSTNAME}/deploy/{PROJECT_NAME}/{deployment_name}/health"
    timeout = time.time() + 300  # Increase timeout to 5 minutes for CI environments
    start = time.time()
    last_status = None
    while time.time() < timeout:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", health_url],
            capture_output=True,
            text=True,
        )
        last_status = result.stdout.strip()
        if last_status == "200":
            return
        time.sleep(5)  # Retry every 5 seconds

    print(
        f"[DEBUG] Health check failed after {time.time() - start:.1f}s for {deployment_name}; last_status={last_status}"
    )
    _run_debug_cmd("curl health verbose", ["curl", "-v", "--max-time", "20", health_url])
    _dump_deployment_debug_info(deployment_name)
    _dump_registry_status()
    raise AssertionError("Model health endpoint did not respond with 200 within 5 minutes")


def test_deployed_model_returns_predictions():
    """Test that deployed model returns predictions."""
    _skip_if_mlflow_not_ready()
    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")
    predict_url = f"http://{MP_HOSTNAME}/deploy/{PROJECT_NAME}/{deployment_name}/predict"

    test_data = {"inputs": {"0": 3, "1": 5.1, "2": 1.4, "3": 0.2}}

    timeout = time.time() + 120  # 2-minute timeout for retries
    start = time.time()
    last_status = None
    last_body = None
    last_error = None
    while time.time() < timeout:
        try:
            response = requests.post(
                predict_url, json=test_data, headers={"Content-Type": "application/json"}, timeout=10
            )
            last_status = response.status_code
            last_body = response.text
            if response.status_code == 200:
                predictions = response.json()
                assert "outputs" in predictions, f"Response should contain outputs or predictions: {predictions}"
                return
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = str(exc)
        time.sleep(5)  # Retry every 5 seconds on connection errors

    print(
        f"[DEBUG] Prediction failed after {time.time() - start:.1f}s for {deployment_name}; "
        f"last_status={last_status}, last_error={last_error}, last_body={last_body}"
    )
    _run_debug_cmd(
        "curl predict verbose",
        ["curl", "-v", "--max-time", "20", "-H", "Content-Type: application/json", "-d", str(test_data), predict_url],
    )
    _dump_deployment_debug_info(deployment_name)
    _dump_registry_status()
    raise AssertionError("Could not get prediction from model within 2 minutes")


def test_list_deployed_models():
    """Test that list deployed models shows the deployed model."""
    _skip_if_mlflow_not_ready()
    result = run_cli("projects", "list-deployed-models", PROJECT_NAME)
    assert result.returncode == 0, f"List deployed models failed: {result.stderr}"
    assert MODEL_NAME in result.stdout or MODEL_NAME.replace("_", "-") in result.stdout


def test_undeploy_model():
    """Test model undeployment."""
    _skip_if_mlflow_not_ready()
    result = run_cli("projects", "undeploy", PROJECT_NAME, "--model-name", MODEL_NAME, "--model-version", MODEL_VERSION)
    assert result.returncode == 0, f"Undeploy failed: {result.stderr}"


def test_undeployed_model_is_removed():
    """Test that undeployed model no longer has a K8s deployment."""
    _skip_if_mlflow_not_ready()
    time.sleep(30)

    deployment_name = sanitize_ressource_name(f"{PROJECT_NAME}-{MODEL_NAME}-{MODEL_VERSION}-deployment")
    result = subprocess.run(
        ["kubectl", "get", "deployment", deployment_name, "-n", PROJECT_NAME],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, f"Deployment {deployment_name} should have been deleted"


def test_delete_project():
    """Test project deletion."""
    result = run_cli("projects", "delete", PROJECT_NAME)
    assert result.returncode == 0, f"Delete failed: {result.stderr}"
    assert "✅ Project deleted successfully" in result.stdout


def test_project_registry_is_removed():
    """Test that project registry is no longer accessible after deletion."""
    time.sleep(60)

    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/"],
        capture_output=True,
        text=True,
    )
    # 404, 502, or 503 all indicate the registry is gone
    assert result.stdout in ["404", "502", "503", "504"], f"Registry should not be accessible: {result.stdout}"
