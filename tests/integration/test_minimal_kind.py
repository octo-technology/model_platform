"""
Minimal integration tests for Kind cluster.

These tests verify basic infrastructure components are working:
- K8s connectivity
- Backend health check
- Basic API responses

Run with: pytest tests/integration/test_minimal_kind.py -v
Requires: Kind cluster with basic infrastructure
"""

import json
import subprocess

import pytest

from tests.conftest import is_kubectl_available


# Skip all tests if no cluster available
pytestmark = pytest.mark.skipif(not is_kubectl_available(), reason="No Kubernetes cluster available")


class TestKubernetesConnectivity:
    """Tests for basic K8s connectivity."""

    def test_kubectl_can_list_namespaces(self):
        """Test that kubectl can list namespaces."""
        result = subprocess.run(
            ["kubectl", "get", "namespaces", "-o", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"kubectl failed: {result.stderr}"
        namespaces = json.loads(result.stdout)
        assert "items" in namespaces

        # Check that at least default namespace exists
        ns_names = [ns["metadata"]["name"] for ns in namespaces["items"]]
        assert "default" in ns_names

    def test_kubectl_can_list_pods(self):
        """Test that kubectl can list pods."""
        result = subprocess.run(
            ["kubectl", "get", "pods", "--all-namespaces", "-o", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"kubectl failed: {result.stderr}"
        pods = json.loads(result.stdout)
        assert "items" in pods


class TestModelPlatformNamespace:
    """Tests for model-platform namespace."""

    def test_model_platform_namespace_exists(self):
        """Test that model-platform namespace exists."""
        result = subprocess.run(
            ["kubectl", "get", "namespace", "model-platform", "-o", "json"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip("model-platform namespace not deployed")

        ns = json.loads(result.stdout)
        assert ns["metadata"]["name"] == "model-platform"

    def test_backend_deployment_exists(self):
        """Test that backend deployment exists in model-platform namespace."""
        result = subprocess.run(
            ["kubectl", "get", "deployment", "backend", "-n", "model-platform", "-o", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Backend deployment not found: {result.stderr}"

        deployment = json.loads(result.stdout)
        assert deployment["metadata"]["name"] == "backend"

    def test_backend_pods_are_running(self):
        """Test that backend pods are running."""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "model-platform", "-l", "app=backend", "-o", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Cannot get backend pods: {result.stderr}"

        pods = json.loads(result.stdout)
        assert pods.get("items"), "No backend pods found"

        for pod in pods["items"]:
            phase = pod["status"]["phase"]
            assert phase in ["Running", "Succeeded"], f"Pod {pod['metadata']['name']} is in phase {phase}"


class TestNginxInfrastructure:
    """Tests for nginx reverse proxy infrastructure."""

    def test_nginx_deployment_exists(self):
        """Test that nginx deployment exists."""
        result = subprocess.run(
            ["kubectl", "get", "deployment", "nginx-reverse-proxy", "-n", "default", "-o", "json"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip("nginx-reverse-proxy deployment not found")

        deployment = json.loads(result.stdout)
        assert deployment["metadata"]["name"] == "nginx-reverse-proxy"

    def test_ingress_exists(self):
        """Test that ingress is configured."""
        result = subprocess.run(
            ["kubectl", "get", "ingress", "-n", "default", "-o", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Failed to get ingress: {result.stderr}"
        ingresses = json.loads(result.stdout)
        assert len(ingresses.get("items", [])) > 0, "No ingress resources found in default namespace"


class TestMinioStorage:
    """Tests for MinIO storage infrastructure."""

    def test_minio_service_exists(self):
        """Test that MinIO service exists."""
        result = subprocess.run(
            ["kubectl", "get", "service", "minio", "-n", "minio", "-o", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"MinIO service not found: {result.stderr}"
        service = json.loads(result.stdout)
        assert service["metadata"]["name"] == "minio"
