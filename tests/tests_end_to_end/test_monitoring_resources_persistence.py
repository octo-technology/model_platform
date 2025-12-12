"""
Test de non-régression : Le Makefile k8s-monitoring est idempotent.

Ce test vérifie que lancer `make k8s-monitoring` ne supprime pas les ressources
de monitoring créées dynamiquement par le backend (ServiceMonitors et dashboards ConfigMaps).

Ce test a été créé suite au bug où les dashboards Grafana affichaient "Dashboard not found"
après un redémarrage de la plateforme, car `make k8s-monitoring` supprimait le namespace
`monitoring` et toutes les ressources qu'il contenait.
"""

import json
import subprocess
import time

import pytest
from loguru import logger


def is_minikube_running():
    """Vérifie si Minikube est en cours d'exécution."""
    try:
        result = subprocess.run(["minikube", "status"], capture_output=True, text=True, check=True)
        return "Running" in result.stdout
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def is_namespace_present(namespace):
    """Vérifie si un namespace Kubernetes existe."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "namespace", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(json.loads(result.stdout))
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def create_test_service_monitor(name, namespace="monitoring"):
    """Crée un ServiceMonitor de test dans le namespace monitoring."""
    service_monitor = {
        "apiVersion": "monitoring.coreos.com/v1",
        "kind": "ServiceMonitor",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app": "test-persistence",
                "release": "kube-prometheus-stack",
            },
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": "test-persistence",
                }
            },
            "endpoints": [
                {
                    "port": "http",
                    "path": "/metrics",
                    "interval": "30s",
                }
            ],
            "namespaceSelector": {"matchNames": ["default"]},
        },
    }

    try:
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=json.dumps(service_monitor),
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Created test ServiceMonitor: {name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create ServiceMonitor: {e.stderr}")
        return False


def create_test_dashboard_configmap(name, namespace="monitoring"):
    """Crée un ConfigMap de dashboard de test dans le namespace monitoring."""
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "grafana_dashboard": "1",
                "app": "test-persistence",
            },
        },
        "data": {
            "test-dashboard.json": json.dumps(
                {
                    "uid": "test-persistence-dashboard",
                    "title": "Test Persistence Dashboard",
                    "panels": [],
                }
            )
        },
    }

    try:
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=json.dumps(configmap),
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Created test ConfigMap: {name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create ConfigMap: {e.stderr}")
        return False


def resource_exists(resource_type, name, namespace="monitoring"):
    """Vérifie si une ressource Kubernetes existe."""
    try:
        result = subprocess.run(
            ["kubectl", "get", resource_type, name, "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(json.loads(result.stdout))
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def delete_resource(resource_type, name, namespace="monitoring"):
    """Supprime une ressource Kubernetes."""
    try:
        subprocess.run(
            ["kubectl", "delete", resource_type, name, "-n", namespace, "--ignore-not-found"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_make_k8s_monitoring():
    """Exécute la target make k8s-monitoring."""
    try:
        result = subprocess.run(
            ["make", "k8s-monitoring"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )
        logger.info(f"make k8s-monitoring stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"make k8s-monitoring stderr: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error("make k8s-monitoring timed out")
        return False
    except FileNotFoundError:
        logger.error("make command not found")
        return False


# Test fixtures
TEST_SERVICE_MONITOR_NAME = "test-persistence-servicemonitor"
TEST_CONFIGMAP_NAME = "grafana-dashboard-test-persistence"


@pytest.fixture(scope="module")
def ensure_minikube_running():
    """Fixture pour s'assurer que Minikube est en cours d'exécution."""
    assert is_minikube_running(), "Minikube n'est pas en cours d'exécution"
    yield


@pytest.fixture(scope="module")
def ensure_monitoring_namespace(ensure_minikube_running):
    """Fixture pour s'assurer que le namespace monitoring existe."""
    assert is_namespace_present("monitoring"), "Le namespace monitoring n'existe pas"
    yield


@pytest.fixture
def cleanup_test_resources():
    """Fixture pour nettoyer les ressources de test après chaque test."""
    yield
    # Cleanup after test
    delete_resource("servicemonitor", TEST_SERVICE_MONITOR_NAME)
    delete_resource("configmap", TEST_CONFIGMAP_NAME)


class TestMonitoringResourcesPersistence:
    """Tests de persistance des ressources de monitoring."""

    def test_monitoring_namespace_exists(self, ensure_monitoring_namespace):
        """Vérifie que le namespace monitoring existe."""
        assert is_namespace_present("monitoring")

    def test_can_create_servicemonitor_in_monitoring_namespace(
        self, ensure_monitoring_namespace, cleanup_test_resources
    ):
        """Vérifie qu'on peut créer un ServiceMonitor dans le namespace monitoring."""
        assert create_test_service_monitor(TEST_SERVICE_MONITOR_NAME)
        assert resource_exists("servicemonitor", TEST_SERVICE_MONITOR_NAME)

    def test_can_create_dashboard_configmap_in_monitoring_namespace(
        self, ensure_monitoring_namespace, cleanup_test_resources
    ):
        """Vérifie qu'on peut créer un ConfigMap de dashboard dans le namespace monitoring."""
        assert create_test_dashboard_configmap(TEST_CONFIGMAP_NAME)
        assert resource_exists("configmap", TEST_CONFIGMAP_NAME)

    @pytest.mark.slow
    @pytest.mark.destructive
    def test_k8s_monitoring_preserves_custom_resources(
        self, ensure_monitoring_namespace, cleanup_test_resources
    ):
        """
        Test principal : Vérifie que `make k8s-monitoring` préserve les ressources personnalisées.

        Ce test :
        1. Crée un ServiceMonitor de test
        2. Crée un ConfigMap de dashboard de test
        3. Exécute `make k8s-monitoring`
        4. Vérifie que les deux ressources existent toujours

        ATTENTION : Ce test exécute réellement `make k8s-monitoring` et peut prendre plusieurs minutes.
        Il est marqué comme @pytest.mark.slow et @pytest.mark.destructive.

        Pour l'exécuter : pytest -m "slow and destructive" tests/tests_end_to_end/test_monitoring_resources_persistence.py
        """
        # Step 1: Create test ServiceMonitor
        assert create_test_service_monitor(TEST_SERVICE_MONITOR_NAME), "Failed to create test ServiceMonitor"
        assert resource_exists(
            "servicemonitor", TEST_SERVICE_MONITOR_NAME
        ), "Test ServiceMonitor was not created"

        # Step 2: Create test dashboard ConfigMap
        assert create_test_dashboard_configmap(TEST_CONFIGMAP_NAME), "Failed to create test ConfigMap"
        assert resource_exists("configmap", TEST_CONFIGMAP_NAME), "Test ConfigMap was not created"

        logger.info("Test resources created, running make k8s-monitoring...")

        # Step 3: Run make k8s-monitoring
        # Note: This may take a few minutes
        monitoring_success = run_make_k8s_monitoring()

        # Wait for resources to stabilize
        time.sleep(30)

        # Step 4: Verify resources still exist
        servicemonitor_exists = resource_exists("servicemonitor", TEST_SERVICE_MONITOR_NAME)
        configmap_exists = resource_exists("configmap", TEST_CONFIGMAP_NAME)

        # Log results for debugging
        logger.info(f"ServiceMonitor exists after k8s-monitoring: {servicemonitor_exists}")
        logger.info(f"ConfigMap exists after k8s-monitoring: {configmap_exists}")

        # Assertions
        assert servicemonitor_exists, (
            "Le ServiceMonitor a été supprimé par `make k8s-monitoring`. "
            "Cela signifie que le namespace monitoring est supprimé et recréé, "
            "ce qui détruit les ressources de monitoring des modèles déployés. "
            "Le Makefile devrait utiliser `helm upgrade --install` au lieu de supprimer le namespace."
        )

        assert configmap_exists, (
            "Le ConfigMap du dashboard a été supprimé par `make k8s-monitoring`. "
            "Cela signifie que le namespace monitoring est supprimé et recréé, "
            "ce qui détruit les dashboards Grafana des modèles déployés. "
            "Le Makefile devrait utiliser `helm upgrade --install` au lieu de supprimer le namespace."
        )


class TestMakefileDoesNotDeleteMonitoringNamespace:
    """
    Test unitaire : Vérifie que le Makefile ne contient pas la commande de suppression du namespace.

    Ce test est plus rapide et peut être exécuté dans la CI sans cluster Kubernetes.
    """

    def test_makefile_does_not_delete_monitoring_namespace(self):
        """
        Vérifie que le Makefile n'utilise pas `kubectl delete namespace monitoring`.

        Si ce test échoue, cela signifie que quelqu'un a réintroduit la commande
        de suppression du namespace monitoring dans le Makefile.
        """
        with open("Makefile", "r") as f:
            makefile_content = f.read()

        # Check for the problematic command
        problematic_commands = [
            "kubectl delete namespace monitoring",
            "kubectl delete ns monitoring",
        ]

        for cmd in problematic_commands:
            assert cmd not in makefile_content, (
                f"Le Makefile contient la commande '{cmd}' qui supprime le namespace monitoring. "
                "Cette commande détruit les ServiceMonitors et dashboards des modèles déployés. "
                "Utilisez `helm upgrade --install` à la place."
            )
