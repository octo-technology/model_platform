"""
Non-regression test: Makefile k8s-monitoring must be idempotent.

Verifies that `make k8s-monitoring` doesn't delete dynamically created
monitoring resources (ServiceMonitors and dashboard ConfigMaps).
"""

import json
import subprocess
import time

import pytest


TEST_SERVICE_MONITOR_NAME = "test-persistence-servicemonitor"
TEST_CONFIGMAP_NAME = "grafana-dashboard-test-persistence"


def run_kubectl(*args, input_data=None):
    try:
        subprocess.run(
            ["kubectl", *args],
            input=input_data,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def resource_exists(resource_type, name, namespace="monitoring"):
    return run_kubectl("get", resource_type, name, "-n", namespace)


def create_test_service_monitor(name, namespace="monitoring"):
    resource = {
        "apiVersion": "monitoring.coreos.com/v1",
        "kind": "ServiceMonitor",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"app": "test-persistence", "release": "kube-prometheus-stack"},
        },
        "spec": {
            "selector": {"matchLabels": {"app": "test-persistence"}},
            "endpoints": [{"port": "http", "path": "/metrics", "interval": "30s"}],
            "namespaceSelector": {"matchNames": ["default"]},
        },
    }
    run_kubectl("apply", "-f", "-", input_data=json.dumps(resource))


def create_test_dashboard_configmap(name, namespace="monitoring"):
    resource = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"grafana_dashboard": "1", "app": "test-persistence"},
        },
        "data": {
            "test-dashboard.json": json.dumps({
                "uid": "test-persistence-dashboard",
                "title": "Test Persistence Dashboard",
                "panels": [],
            })
        },
    }
    run_kubectl("apply", "-f", "-", input_data=json.dumps(resource))


def delete_resource(resource_type, name, namespace="monitoring"):
    run_kubectl("delete", resource_type, name, "-n", namespace, "--ignore-not-found")


def run_make_k8s_monitoring():
    subprocess.run(["make", "k8s-monitoring"], capture_output=True, timeout=300)


@pytest.mark.slow
@pytest.mark.destructive
def test_k8s_monitoring_preserves_custom_resources():
    """
    Verifies `make k8s-monitoring` preserves custom resources.

    Run with: pytest -m "slow and destructive" path/to/this/file.py
    """
    create_test_service_monitor(TEST_SERVICE_MONITOR_NAME)
    create_test_dashboard_configmap(TEST_CONFIGMAP_NAME)

    run_make_k8s_monitoring()
    time.sleep(30)

    assert resource_exists("servicemonitor", TEST_SERVICE_MONITOR_NAME), (
        "ServiceMonitor deleted by `make k8s-monitoring`. "
        "Use `helm upgrade --install` instead of deleting the namespace."
    )
    assert resource_exists("configmap", TEST_CONFIGMAP_NAME), (
        "Dashboard ConfigMap deleted by `make k8s-monitoring`. "
        "Use `helm upgrade --install` instead of deleting the namespace."
    )

    delete_resource("servicemonitor", TEST_SERVICE_MONITOR_NAME)
    delete_resource("configmap", TEST_CONFIGMAP_NAME)
