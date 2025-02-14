import json
import subprocess
import time

import mlflow
import mlflow.sklearn
import requests
from loguru import logger
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from model_platform.domain.entities.docker.task_build_statuses import TaskBuildStatuses
from model_platform.utils import sanitize_name


def is_ingress_present(ingress_name="registry-ingress", namespace="default"):
    try:
        # Run kubectl command to get ingress details in JSON format
        result = subprocess.run(
            ["kubectl", "get", "ingress", ingress_name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse JSON output (if command succeeds, ingress exists)
        ingress_data = json.loads(result.stdout)
        return bool(ingress_data)  # True if ingress exists, False otherwise

    except subprocess.CalledProcessError:
        return False  # The ingress doesn't exist or kubectl command failed
    except FileNotFoundError:
        return False


def is_minikube_running():
    try:
        result = subprocess.run(["minikube", "status"], capture_output=True, text=True, check=True)
        return "Running" in result.stdout
    except subprocess.CalledProcessError:
        return False  # La commande a échoué, probablement Minikube n'est pas démarré
    except FileNotFoundError:
        return False  # Minikube n'est pas installé


def is_deployment_present(deployment_name="nginx-reverse-proxy", namespace="default"):
    try:
        # Run kubectl command to get deployment details in JSON format
        result = subprocess.run(
            ["kubectl", "get", "deployment", deployment_name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse JSON output (if command succeeds, deployment exists)
        deployment_data = json.loads(result.stdout)
        return bool(deployment_data)  # True if deployment exists, False otherwise

    except subprocess.CalledProcessError:
        return False  # The deployment doesn't exist or kubectl command failed
    except FileNotFoundError:
        return False  # kubectl is not installed


def is_url_reachable(url):
    try:
        response = requests.get(url, timeout=5)  # Timeout to avoid long waits
        return response.status_code == 200
    except requests.RequestException:
        logger.error(f"Failed to reach URL: {url}")
        return False


def send_post_request(url, data, headers=None, timeout=5):
    try:
        # Default headers if none provided
        if headers is None:
            headers = {"Content-Type": "application/json"}

        # Send POST request
        response = requests.post(url, json=data, headers=headers, timeout=timeout)

        return {"status_code": response.status_code, "response": response.text}

    except requests.RequestException as e:
        return {"error": str(e)}


def send_get_request(url, params=None, headers=None, timeout=5):
    try:
        # Send GET request
        response = requests.get(url, params=params, headers=headers, timeout=timeout)

        return {"status_code": response.status_code, "response": response.text}

    except requests.RequestException as e:
        return {"error": str(e)}


def test_if_test_env_is_running():
    assert is_minikube_running()
    assert is_ingress_present()
    assert is_deployment_present()
    ## check if backend is reachable
    assert is_url_reachable("http://localhost:8001/health")


PROJECT_NAME = "test"
MODEL_NAME = "test_model"


def test_project_creation_should_respond_correctly():
    project_json = {
        "name": PROJECT_NAME,
        "owner": "Test Owner",
        "scope": "Test Scope",
        "data_perimeter": "test data perimeter",
    }
    status_project_creation = requests.post(
        "http://localhost:8001/projects/add",
        json=project_json,
        headers={"Content-Type": "application/json"},  # Ensure proper header
    )
    assert status_project_creation.status_code == 200


def test_project_list_should_return_created_project():
    status_project_list = requests.get("http://localhost:8001/projects/list")
    assert status_project_list.status_code == 200
    assert len(status_project_list.json()) > 0
    assert status_project_list.json()[0]["name"] == PROJECT_NAME


def test_project_should_have_responding_mlflow_registry():
    time.sleep(60)
    status_project_registry = requests.get(f"http://model-platform.com/registry/{PROJECT_NAME}/")
    assert status_project_registry.status_code == 200


def test_project_train_model_should_push_model_to_mlflow():
    data = load_iris()
    x = data.data
    y = data.target
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
    mlflow.set_tracking_uri(f"http://model-platform.com/registry/{PROJECT_NAME}/")
    with mlflow.start_run():
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        accuracy = accuracy_score(y_test, y_pred)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.sklearn.log_model(model, "custom_model", registered_model_name=MODEL_NAME)

        print(f"Model Accuracy: {accuracy}")
        print("Model saved to MLflow!")

    model_list = requests.get(f"http://localhost:8001/{PROJECT_NAME}/models/list")
    model_list = json.loads(model_list.text)
    model_names = [model["name"] for model in model_list]
    assert "test_model" in model_names


def test_deploy_model_should_deploy_healthy_model():
    model_name = sanitize_name(MODEL_NAME)
    status_query = requests.get(f"http://localhost:8001/{PROJECT_NAME}/models/deploy/{MODEL_NAME}/1")
    assert status_query.status_code == 200
    json_result = json.loads(status_query.text)
    task_id = json_result["task_id"]
    status = json_result["status"]
    assert status == "Deployment initiated"
    while status not in [TaskBuildStatuses.completed, TaskBuildStatuses.failed]:
        status_query = requests.get(f"http://localhost:8001/{PROJECT_NAME}/models/task-status/{task_id}")
        json_result = json.loads(status_query.text)
        status = json_result["status"]
        time.sleep(5)
    time.sleep(60)
    deploy_status = requests.get(
        f"http://model-platform.com/deploy/{PROJECT_NAME}/{PROJECT_NAME}-{model_name}-1-deployment/health"
    )
    assert deploy_status.status_code == 200
    assert json.loads(deploy_status.text)["status"] == "healthy"


def test_undeploy_model_should_undeploy_correctly():
    model_name = sanitize_name(MODEL_NAME)
    status_query = requests.get(f"http://localhost:8001/{PROJECT_NAME}/models/undeploy/{MODEL_NAME}/1")
    assert status_query.status_code == 200
    time.sleep(60)
    deploy_status = requests.get(
        f"http://model-platform.com/deploy/{PROJECT_NAME}/{PROJECT_NAME}-{model_name}-1-deployment/health"
    )
    assert deploy_status.status_code == 502


def test_remove_project_should_correctly_remove_project_registry():
    status_query = requests.get(f"http://localhost:8001/projects/{PROJECT_NAME}/remove")
    assert status_query.status_code == 200
    time.sleep(60)
    status_project_registry = requests.get(f"http://model-platform.com/registry/{PROJECT_NAME}/")
    assert status_project_registry.status_code == 502
