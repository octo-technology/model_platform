# Philippe Stepniewski
"""
End-to-end test: Batch prediction workflow.

This test covers:
1. Project creation with batch enabled
2. Model training and push to MLflow
3. Batch prediction submission (triggers auto-build of Docker image)
4. Status polling until completion
5. Result download and validation
6. Cleanup (delete job + files + project)
"""

import os
import random
import string
import subprocess
import sys
import time

import mlflow
import mlflow.sklearn
import pytest
import requests
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from tests.conftest import MP_HOSTNAME, cleanup_project, login, run_cli

_this_module = sys.modules[__name__]

PROJECT_SUFFIX = "".join(random.choices(string.ascii_lowercase, k=6))
PROJECT_NAME = f"e2ebatch{PROJECT_SUFFIX}"
MODEL_NAME = "batch_test_model"
MODEL_VERSION = "1"


def _setup_minikube_docker_env():
    try:
        result = subprocess.run(
            ["minikube", "docker-env", "--shell", "bash"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            env_lines = [line.strip() for line in result.stdout.split("\n") if line.startswith("export ")]
            for line in env_lines:
                var_assignment = line.replace("export ", "", 1)
                if "=" in var_assignment:
                    key, value = var_assignment.split("=", 1)
                    value = value.strip("\"'")
                    os.environ[key] = value
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
    except Exception as exc:  # noqa: BLE001
        print(f"[DEBUG] {label} error: {exc}")


def _dump_batch_debug_info():
    _run_debug_cmd("kubectl get jobs", ["kubectl", "get", "jobs", "-n", PROJECT_NAME, "-o", "wide"])
    _run_debug_cmd("kubectl get pods", ["kubectl", "get", "pods", "-n", PROJECT_NAME, "-o", "wide"])
    _run_debug_cmd(
        "kubectl get events",
        ["kubectl", "get", "events", "-n", PROJECT_NAME, "--sort-by=.metadata.creationTimestamp"],
    )
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", PROJECT_NAME, "-l", "app=batch-prediction", "--no-headers"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode == 0 and result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            pod_name = line.split()[0]
            _run_debug_cmd(f"kubectl logs {pod_name}", ["kubectl", "logs", pod_name, "-n", PROJECT_NAME, "--tail=50"])


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    print(f"[DEBUG] Setting up batch e2e test with project {PROJECT_NAME}")
    _setup_minikube_docker_env()
    assert login() == 0, "Login failed"

    yield

    cleanup_project(PROJECT_NAME)


# ── Track readiness (set via module attribute for robustness) ────
_mlflow_ready = False


def _skip_if_mlflow_not_ready():
    if not getattr(_this_module, "_mlflow_ready", False):
        pytest.skip("MLflow registry not ready")


# ── Tests (ordered) ──────────────────────────────────────────────


@pytest.mark.order(1)
def test_create_project_with_batch():
    result = run_cli("projects", "add", "--name", PROJECT_NAME, "--batch-enabled")
    assert result.returncode == 0, f"Project creation failed: {result.stderr}"
    assert "Project created successfully" in result.stdout


@pytest.mark.order(2)
def test_mlflow_registry_responds():
    registry_url = f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/"
    deadline = time.time() + 300
    while time.time() < deadline:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", registry_url],
            capture_output=True,
            text=True,
        )
        if result.stdout == "200":
            _this_module._mlflow_ready = True
            return
        print(f"[DEBUG] MLflow registry HTTP {result.stdout}, retrying in 5s...")
        time.sleep(5)
    assert False, "MLflow registry did not respond with 200 within 5 minutes"


@pytest.mark.order(3)
def test_train_and_push_model():
    _skip_if_mlflow_not_ready()
    api_url = f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/api/2.0/mlflow/experiments/search"
    response = requests.post(api_url, json={"max_results": 1}, timeout=10)
    assert response.status_code == 200, f"MLflow API not ready: {response.status_code}"

    data = load_iris()
    x_train, _, y_train, _ = train_test_split(data.data, data.target, test_size=0.3, random_state=42)

    mlflow.set_tracking_uri(f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/")

    with mlflow.start_run():
        model = RandomForestClassifier(n_estimators=2, random_state=42)
        model.fit(x_train, y_train)
        mlflow.sklearn.log_model(model, "custom_model", registered_model_name=MODEL_NAME)

    deadline = time.time() + 60
    while time.time() < deadline:
        result = run_cli("projects", "list-models", PROJECT_NAME)
        if result.returncode == 0 and MODEL_NAME in result.stdout:
            return
        time.sleep(5)
    assert False, f"Model {MODEL_NAME} not found after 60s"


@pytest.mark.order(4)
def test_submit_batch_prediction():
    """Submit a batch prediction via the API. This triggers auto-build of the Docker image."""
    _skip_if_mlflow_not_ready()

    # Create a small CSV matching the iris model (4 features)
    csv_content = "0,1,2,3\n5.1,3.5,1.4,0.2\n6.2,2.9,4.3,1.3\n7.1,3.0,5.9,2.1\n"
    csv_path = f"/tmp/batch_e2e_test_{PROJECT_NAME}.csv"
    with open(csv_path, "w") as f:
        f.write(csv_content)

    result = run_cli("batch", "submit", PROJECT_NAME, MODEL_NAME, MODEL_VERSION, "--file-path", csv_path)
    assert result.returncode == 0, f"Batch submit failed: {result.stderr}\n{result.stdout}"
    assert "Job ID:" in result.stdout or "job_id" in result.stdout

    # Extract job_id from output
    for line in result.stdout.splitlines():
        if "Job ID:" in line:
            _this_module._batch_job_id = line.split("Job ID:")[-1].strip()
            print(f"[DEBUG] Batch job submitted with ID: {_this_module._batch_job_id}")
            return

    assert False, f"Could not extract job ID from output: {result.stdout}"


_batch_job_id = None


def _skip_if_no_job():
    if not getattr(_this_module, "_batch_job_id", None):
        pytest.skip("No batch job ID available")


@pytest.mark.order(5)
def test_batch_job_completes():
    """Poll batch job status until it completes (building → pending → running → completed)."""
    _skip_if_mlflow_not_ready()
    _skip_if_no_job()

    deadline = time.time() + 600  # 10 minutes — includes Docker image build
    last_status = None
    while time.time() < deadline:
        result = run_cli("batch", "status", PROJECT_NAME, _this_module._batch_job_id)
        output = result.stdout.lower()

        if "completed" in output:
            print(f"[DEBUG] Batch job {_this_module._batch_job_id} completed")
            return

        if "failed" in output:
            print(f"[DEBUG] Batch job {_this_module._batch_job_id} FAILED")
            _dump_batch_debug_info()
            assert False, f"Batch job failed: {result.stdout}"

        # Extract status for debug
        for status_word in ["building", "pending", "running"]:
            if status_word in output:
                if status_word != last_status:
                    print(f"[DEBUG] Batch job status: {status_word}")
                    last_status = status_word
                break

        time.sleep(10)

    _dump_batch_debug_info()
    assert False, f"Batch job did not complete within 10 minutes. Last status: {last_status}"


@pytest.mark.order(6)
def test_download_batch_result():
    """Download the batch prediction result and validate it."""
    _skip_if_mlflow_not_ready()
    _skip_if_no_job()

    output_path = f"/tmp/batch_e2e_result_{PROJECT_NAME}.csv"
    result = run_cli("batch", "download", PROJECT_NAME, _this_module._batch_job_id, "--output", output_path)
    assert result.returncode == 0, f"Download failed: {result.stderr}\n{result.stdout}"
    assert "downloaded" in result.stdout.lower()

    assert os.path.exists(output_path), f"Output file not found at {output_path}"
    with open(output_path) as f:
        lines = f.readlines()
    # Header + 3 prediction rows
    assert len(lines) >= 4, f"Expected at least 4 lines (header + 3 rows), got {len(lines)}: {lines}"
    assert "prediction" in lines[0].lower(), f"Expected 'prediction' header, got: {lines[0]}"
    print(f"[DEBUG] Downloaded {len(lines) - 1} predictions")


@pytest.mark.order(7)
def test_list_batch_jobs():
    """Verify the job appears in the list."""
    _skip_if_mlflow_not_ready()
    _skip_if_no_job()

    result = run_cli("batch", "list", PROJECT_NAME)
    assert result.returncode == 0, f"List failed: {result.stderr}"
    assert (
        _this_module._batch_job_id in result.stdout
    ), f"Job {_this_module._batch_job_id} not in list output: {result.stdout}"


@pytest.mark.order(8)
def test_delete_batch_job():
    """Delete the batch job and associated files."""
    _skip_if_mlflow_not_ready()
    _skip_if_no_job()

    result = run_cli("batch", "delete", PROJECT_NAME, _this_module._batch_job_id)
    assert result.returncode == 0, f"Delete failed: {result.stderr}\n{result.stdout}"
    assert "deleted" in result.stdout.lower()


@pytest.mark.order(9)
def test_delete_project():
    result = run_cli("projects", "delete", PROJECT_NAME)
    assert result.returncode == 0, f"Delete failed: {result.stderr}"
    assert "Project deleted successfully" in result.stdout
