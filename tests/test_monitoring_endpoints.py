"""Test monitoring endpoints for dashboard data retrieval."""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app


@pytest.fixture
def client():
    """Create test client with app."""
    app = create_app()
    return TestClient(app)


def test_monitoring_deployments_endpoint(client):
    """Test GET /metrics/monitoring/deployments returns list of deployments."""
    response = client.get("/metrics/monitoring/deployments")

    # Should succeed (200) or return empty list if no deployments
    assert response.status_code in [200, 503]  # 503 if Prometheus unavailable

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

        # If there are deployments, check structure
        if len(data) > 0:
            deployment = data[0]
            assert "id" in deployment
            assert "name" in deployment
            assert "version" in deployment
            assert "project" in deployment
            assert "deployment_name" in deployment
            assert "status" in deployment


def test_monitoring_projects_endpoint(client):
    """Test GET /metrics/monitoring/projects returns list of projects."""
    response = client.get("/metrics/monitoring/projects")

    # Should succeed (200)
    assert response.status_code in [200, 503]  # 503 if DB unavailable

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
