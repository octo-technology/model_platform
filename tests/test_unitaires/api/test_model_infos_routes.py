# Philippe Stepniewski
import os

os.environ.setdefault("PATH_LOG_EVENTS", "/tmp/test_log_events")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.model_infos_routes import get_model_info_db_handler
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter


@pytest.fixture
def mock_handler():
    return MagicMock()


@pytest.fixture
def client(mock_handler):
    app = create_app()
    app.dependency_overrides[get_model_info_db_handler] = lambda: mock_handler
    app.dependency_overrides[get_current_user] = lambda: {"id": "user123", "username": "test_user"}
    app.dependency_overrides[get_user_adapter] = lambda: MagicMock()
    with patch("backend.api.model_infos_routes.user_can_perform_action_for_project"):
        yield TestClient(app)


class TestAcceptRiskLevel:
    def test_accept_risk_level_success(self, client, mock_handler):
        mock_handler.update_risk_level.return_value = True

        response = client.post(
            "/model_infos/my_project/my_model/1/accept_risk_level",
            json={"risk_level": "high"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["risk_level"] == "high"
        mock_handler.update_risk_level.assert_called_once_with("my_model", "1", "my_project", "high")

    def test_accept_risk_level_normalizes_input(self, client, mock_handler):
        response = client.post(
            "/model_infos/my_project/my_model/1/accept_risk_level",
            json={"risk_level": "  HIGH  "},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "high"
        mock_handler.update_risk_level.assert_called_once_with("my_model", "1", "my_project", "high")

    def test_accept_risk_level_all_valid_levels(self, client, mock_handler):
        for level in ["unacceptable", "high", "limited", "minimal"]:
            mock_handler.reset_mock()

            response = client.post(
                "/model_infos/proj/model/1/accept_risk_level",
                json={"risk_level": level},
            )

            assert response.status_code == 200, f"Failed for level: {level}"
            assert response.json()["risk_level"] == level

    def test_accept_risk_level_invalid_level_returns_400(self, client):
        response = client.post(
            "/model_infos/my_project/my_model/1/accept_risk_level",
            json={"risk_level": "critical"},
        )

        assert response.status_code == 400
        assert "Invalid risk level" in response.json()["detail"]

    def test_accept_risk_level_empty_string_returns_400(self, client):
        response = client.post(
            "/model_infos/my_project/my_model/1/accept_risk_level",
            json={"risk_level": ""},
        )

        assert response.status_code == 400

    def test_accept_risk_level_missing_body_returns_422(self, client):
        response = client.post(
            "/model_infos/my_project/my_model/1/accept_risk_level",
        )

        assert response.status_code == 422
