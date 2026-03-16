"""Integration tests for metrics API endpoints.

Tests the full flow from HTTP request to response, including
route handling, use case execution, and dependency injection.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from backend.api.app import create_app
from backend.domain.entities.metrics import ModelMetrics, FleetMetrics


@pytest.fixture
def client():
    """Create test client with mocked app."""
    app = create_app()
    return TestClient(app)


def test_get_model_metrics_success(client):
    """Test successful model metrics retrieval."""
    mock_result = {
        "success_rate": 93.5,
        "error_rate": 6.5,
        "total_calls": 45000,
        "total_errors": 2925,
    }

    with patch("backend.api.metrics_routes.metrics_usecases.get_model_metrics", new_callable=AsyncMock) as mock_usecase:
        mock_usecase.return_value = ModelMetrics(
            model_id="credit-v2-prod",
            project_name="Banking",
            period="7d",
            **mock_result,
        )

        response = client.get("/metrics/models/credit-v2-prod?period=7d")

        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] == "credit-v2-prod"
        assert data["success_rate"] == 93.5
        assert data["error_rate"] == 6.5
        assert data["total_calls"] == 45000
        assert data["total_errors"] == 2925


def test_get_model_metrics_not_found(client):
    """Test 404 response when model not found."""
    with patch("backend.api.metrics_routes.metrics_usecases.get_model_metrics", new_callable=AsyncMock) as mock_usecase:
        mock_usecase.side_effect = ValueError("Model not found")

        response = client.get("/metrics/models/unknown-model?period=7d")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_model_metrics_invalid_period(client):
    """Test validation error for invalid period parameter."""
    response = client.get("/metrics/models/credit-v2-prod?period=invalid")

    assert response.status_code == 422  # Validation error


def test_get_model_metrics_default_period(client):
    """Test that default period is 7d."""
    with patch("backend.api.metrics_routes.metrics_usecases.get_model_metrics") as mock_usecase:
        mock_usecase.return_value = ModelMetrics(
            model_id="model123",
            project_name="test",
            period="7d",
            success_rate=95.0,
            error_rate=5.0,
            total_calls=1000,
            total_errors=50,
        )

        response = client.get("/metrics/models/model123")

        assert response.status_code == 200
        # Verify use case was called with default period
        mock_usecase.assert_called_once()
        call_kwargs = mock_usecase.call_args[1]
        assert call_kwargs["period"] == "7d"


def test_get_model_metrics_prometheus_unavailable(client):
    """Test 503 response when Prometheus unavailable."""
    with patch("backend.api.metrics_routes.metrics_usecases.get_model_metrics") as mock_usecase:
        mock_usecase.side_effect = Exception("Connection refused")

        response = client.get("/metrics/models/credit-v2-prod")

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()


def test_get_fleet_metrics_success(client):
    """Test successful fleet metrics retrieval."""
    with (
        patch("backend.api.metrics_routes.get_current_user") as mock_auth,
        patch("backend.api.metrics_routes.get_user_adapter") as mock_user_adapter,
        patch("backend.api.metrics_routes.metrics_usecases.get_fleet_metrics") as mock_usecase,
    ):
        mock_auth.return_value = {"id": "user123", "username": "test_user"}
        mock_user_adapter.return_value = MagicMock()

        mock_usecase.return_value = FleetMetrics(
            total_models=6,
            healthy_count=5,
            caution_count=1,
            alert_count=0,
            total_calls=250000,
            period="7d",
        )

        response = client.get("/metrics/fleet?period=7d")

        assert response.status_code == 200
        data = response.json()
        assert data["total_models"] == 6
        assert data["healthy_count"] == 5
        assert data["caution_count"] == 1
        assert data["alert_count"] == 0
        assert data["total_calls"] == 250000


def test_get_fleet_metrics_with_project_filter(client):
    """Test fleet metrics with project name filter."""
    with (
        patch("backend.api.metrics_routes.get_current_user") as mock_auth,
        patch("backend.api.metrics_routes.get_user_adapter") as mock_user_adapter,
        patch("backend.api.metrics_routes.user_can_perform_action_for_project") as mock_permission,
        patch("backend.api.metrics_routes.metrics_usecases.get_fleet_metrics") as mock_usecase,
    ):
        mock_auth.return_value = {"id": "user123"}
        mock_user_adapter.return_value = MagicMock()
        mock_permission.return_value = None  # Permission granted

        mock_usecase.return_value = FleetMetrics(
            total_models=3,
            healthy_count=3,
            caution_count=0,
            alert_count=0,
            total_calls=100000,
            period="7d",
        )

        response = client.get("/metrics/fleet?project_name=Banking&period=7d")

        assert response.status_code == 200
        data = response.json()
        assert data["total_models"] == 3

        # Verify permission check was called
        mock_permission.assert_called_once()


def test_get_fleet_metrics_requires_auth(client):
    """Test that fleet endpoint requires authentication."""
    with patch("backend.api.metrics_routes.get_current_user") as mock_auth:
        mock_auth.side_effect = Exception("Not authenticated")

        response = client.get("/metrics/fleet")

        # Should fail auth check (depends on auth implementation)
        assert response.status_code != 200


def test_get_fleet_metrics_all_periods(client):
    """Test fleet metrics with different periods."""
    periods = ["1d", "7d", "30d", "90d"]

    for period in periods:
        with (
            patch("backend.api.metrics_routes.get_current_user") as mock_auth,
            patch("backend.api.metrics_routes.get_user_adapter") as mock_user_adapter,
            patch("backend.api.metrics_routes.metrics_usecases.get_fleet_metrics") as mock_usecase,
        ):
            mock_auth.return_value = {"id": "user123"}
            mock_user_adapter.return_value = MagicMock()

            mock_usecase.return_value = FleetMetrics(
                total_models=1,
                healthy_count=1,
                caution_count=0,
                alert_count=0,
                total_calls=100,
                period=period,
            )

            response = client.get(f"/metrics/fleet?period={period}")

            assert response.status_code == 200
            call_kwargs = mock_usecase.call_args[1]
            assert call_kwargs["period"] == period
