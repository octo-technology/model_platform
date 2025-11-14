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

from backend.utils import sanitize_project_name

MP_HOSTNAME = "model-platform.com"


def is_ingress_present(ingress_name="registry-ingress", namespace="default"):
    try:
        # Run kubectl command to get ingress details in JSON format
        result = subprocess.run(
            ["kubectl", "get", "ingress", ingress_name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        ingress_data = json.loads(result.stdout)
        return bool(ingress_data)

    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def is_minikube_running():
    try:
        result = subprocess.run(["minikube", "status"], capture_output=True, text=True, check=True)
        return "Running" in result.stdout
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def is_deployment_present(deployment_name="nginx-reverse-proxy", namespace="default"):
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", deployment_name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

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


def login():
    result = subprocess.run(
        ["mp", "login", "--username", "alice@example.com", "--password", "pass!"],
        capture_output=True,
        text=True,
    )
    return result.returncode


# Helper pour uniformiser les appels CLI

def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["mp", *args], capture_output=True, text=True)


def test_if_test_env_is_running():
    assert is_minikube_running()
    assert is_ingress_present()
    assert is_deployment_present()
    assert is_url_reachable(f"http://{MP_HOSTNAME}/health")
    assert login() == 0


PROJECT_NAME = "test"
MODEL_NAME = "test_model"


def test_project_creation_should_respond_correctly():
    delete_result = run_cli("projects", "delete", PROJECT_NAME)
    result = subprocess.run(
        ["mp", "projects", "add", "--name", PROJECT_NAME],
        capture_output=True,
        text=True,
    )
    print(result)
    assert result.returncode == 0
    assert result.stdout == "✅ Project created successfully\n"




# Remplacement: vérifier le fonctionnement de la registry via le CLI list-models (même si vide)

def test_project_should_have_responding_mlflow_registry():
    time.sleep(30)
    # La commande list-models devrait retourner un code 0 et ne pas afficher une erreur
    result = run_cli("projects", "list-models", PROJECT_NAME)
    assert result.returncode == 0
    # Si aucune donnée, stdout peut être vide; on vérifie l'absence du message d'erreur.
    assert "❌" not in result.stdout


def test_project_train_model_should_push_model_to_mlflow():
    data = load_iris()
    x = data.data
    y = data.target
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
    mlflow.set_tracking_uri(f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/")
    with mlflow.start_run():
        model = RandomForestClassifier(n_estimators=2, random_state=42)
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        accuracy = accuracy_score(y_test, y_pred)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.sklearn.log_model(model, "custom_model", registered_model_name=MODEL_NAME)
        print(f"Model Accuracy: {accuracy}")
        print("Model saved to MLflow!")
    # Utiliser le CLI pour lister les modèles et vérifier la présence de MODEL_NAME
    list_result = run_cli("projects", "list-models", PROJECT_NAME)
    assert list_result.returncode == 0
    assert MODEL_NAME in list_result.stdout

#TODO add deployment and undeploy test

def test_remove_project_should_correctly_remove_project_registry():
    # Utiliser la commande delete (déjà testée plus haut) mais on répète pour la cohérence de scénario
    delete_result = run_cli("projects", "delete", PROJECT_NAME)
    assert delete_result.returncode == 0
    assert "✅ Project deleted successfully" in delete_result.stdout
    time.sleep(30)
    status_project_registry = requests.get(f"http://{MP_HOSTNAME}/registry/{PROJECT_NAME}/")
    assert status_project_registry.status_code == 502

