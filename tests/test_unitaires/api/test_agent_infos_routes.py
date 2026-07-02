import os

os.environ.setdefault("PATH_LOG_EVENTS", "/tmp/test_log_events")

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.agent_infos_routes import get_agent_info_db_handler
from backend.domain.entities.agent_info import AgentInfo, AgentTool
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.infrastructure.agent_info_sqlite_db_handler import AgentInfoDoesntExistError


@pytest.fixture
def mock_handler():
    return MagicMock()


@pytest.fixture
def client(mock_handler):
    app = create_app()
    app.dependency_overrides[get_agent_info_db_handler] = lambda: mock_handler
    app.dependency_overrides[get_current_user] = lambda: {"id": "user123", "username": "test_user"}
    app.dependency_overrides[get_user_adapter] = lambda: MagicMock()
    with patch("backend.api.agent_infos_routes.user_can_perform_action_for_project"):
        yield TestClient(app)


class TestGetAgentInfo:
    def test_get_agent_info_success(self, client, mock_handler):
        mock_handler.get_agent_info.return_value = AgentInfo(
            agent_name="my_agent",
            agent_version="1",
            project_name="my_project",
            description="An agent",
            tools=[AgentTool(name="run_sql", description="Runs a read-only SQL query")],
            guardrails="Read-only access",
            risk_level="limited",
        )

        response = client.get("/agent_infos/my_project/my_agent/1")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "my_agent"
        assert data["agent_version"] == "1"
        assert data["tools"] == [{"name": "run_sql", "description": "Runs a read-only SQL query"}]
        assert data["guardrails"] == "Read-only access"
        assert data["risk_level"] == "limited"
        mock_handler.get_agent_info.assert_called_once_with("my_agent", "1", "my_project")

    def test_get_agent_info_not_found_returns_404(self, client, mock_handler):
        mock_handler.get_agent_info.side_effect = AgentInfoDoesntExistError(
            message="AgentInfo doesn't exist",
            agent_name="missing_agent",
            agent_version="1",
            project_name="my_project",
        )

        response = client.get("/agent_infos/my_project/missing_agent/1")

        assert response.status_code == 404
