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


MODEL_VERSION = "1"


def test_deploy_model_should_initiate_deployment():
    """Test that deploying a model initiates the deployment process."""
    result = run_cli("models", "deploy", PROJECT_NAME, "--model-name", MODEL_NAME, "--model-version", MODEL_VERSION)

    assert result.returncode == 0, f"Deploy failed: {result.stderr}"
    assert "✅ Model deployed successfully" in result.stdout or "Deployment initiated" in result.stdout


def wait_for_deployment_ready(deployment_name: str, namespace: str, timeout: int = 300) -> bool:
    """Wait for a K8s deployment to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployment", deployment_name, "-n", namespace, "-o", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            deployment = json.loads(result.stdout)
            status = deployment.get("status", {})
            ready_replicas = status.get("readyReplicas", 0)
            replicas = status.get("replicas", 1)
            if ready_replicas >= replicas and ready_replicas > 0:
                return True
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        time.sleep(10)
    return False


def get_deployed_model_service(project_name: str, model_name: str, version: str) -> dict | None:
    """Get the deployed model service from K8s."""
    # Service name format: {project}-{model}-v{version}
    service_name = f"{project_name}-{model_name.replace('_', '-')}-v{version}"
    try:
        result = subprocess.run(
            ["kubectl", "get", "service", service_name, "-n", project_name, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def test_deployed_model_should_have_running_deployment():
    """Test that deployed model has a running K8s deployment."""
    # Wait for deployment to be ready (model build and deploy can take time)
    deployment_name = f"{PROJECT_NAME}-{MODEL_NAME.replace('_', '-')}-v{MODEL_VERSION}"

    is_ready = wait_for_deployment_ready(deployment_name, PROJECT_NAME, timeout=300)
    assert is_ready, f"Deployment {deployment_name} did not become ready within timeout"


def test_deployed_model_should_respond_to_health_check():
    """Test that deployed model responds to health check."""
    # The model endpoint should be accessible via the ingress
    model_endpoint = f"http://{MP_HOSTNAME}/models/{PROJECT_NAME}/{MODEL_NAME}/v{MODEL_VERSION}/health"

    # Retry several times as the service might take a moment to be fully available
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(model_endpoint, timeout=10)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(10)

    # If direct health endpoint fails, try inference endpoint
    invocations_endpoint = f"http://{MP_HOSTNAME}/models/{PROJECT_NAME}/{MODEL_NAME}/v{MODEL_VERSION}/invocations"
    response = requests.post(
        invocations_endpoint,
        json={"data": [[5.1, 3.5, 1.4, 0.2]]},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert response.status_code in [200, 400], f"Model endpoint not responding: {response.status_code}"


def test_deployed_model_should_return_predictions():
    """Test that deployed model returns predictions for valid input."""
    invocations_endpoint = f"http://{MP_HOSTNAME}/models/{PROJECT_NAME}/{MODEL_NAME}/v{MODEL_VERSION}/invocations"

    # Iris dataset format: 4 features
    test_data = {"data": [[5.1, 3.5, 1.4, 0.2], [6.2, 3.4, 5.4, 2.3]]}

    response = requests.post(
        invocations_endpoint, json=test_data, headers={"Content-Type": "application/json"}, timeout=30
    )

    assert response.status_code == 200, f"Prediction failed: {response.text}"
    predictions = response.json()
    assert "predictions" in predictions or isinstance(predictions, list), "Response should contain predictions"


def test_list_deployed_models_should_show_deployed_model():
    """Test that list deployed models shows the deployed model."""
    result = run_cli("models", "list-deployed", PROJECT_NAME)

    assert result.returncode == 0, f"List deployed models failed: {result.stderr}"
    assert MODEL_NAME in result.stdout or "test_model" in result.stdout


def test_undeploy_model_should_succeed():
    """Test that undeploying a model succeeds."""
    result = run_cli("models", "undeploy", PROJECT_NAME, "--model-name", MODEL_NAME, "--model-version", MODEL_VERSION)

    assert result.returncode == 0, f"Undeploy failed: {result.stderr}"
    assert "✅ Model undeployed successfully" in result.stdout or "return_code" in result.stdout


def test_undeployed_model_should_not_have_deployment():
    """Test that undeployed model no longer has a K8s deployment."""
    # Wait for cleanup
    time.sleep(30)

    deployment_name = f"{PROJECT_NAME}-{MODEL_NAME.replace('_', '-')}-v{MODEL_VERSION}"
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
    invocations_endpoint = f"http://{MP_HOSTNAME}/models/{PROJECT_NAME}/{MODEL_NAME}/v{MODEL_VERSION}/invocations"

    try:
        response = requests.post(
            invocations_endpoint,
            json={"data": [[5.1, 3.5, 1.4, 0.2]]},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        # Should get 502/503/504 (service unavailable) or 404
        assert response.status_code in [404, 502, 503, 504], f"Endpoint should not be available: {response.status_code}"
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
    assert status_project_registry.status_code == 502
