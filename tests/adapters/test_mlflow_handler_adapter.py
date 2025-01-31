import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch
from model_platform.infrastructure.mlflow_handler_adapter import MLFlowHandlerAdapter


@pytest.fixture
def mock_mlflow_client():
    with patch("model_platform.infrastructure.mlflow_handler_adapter.MLflowClientManager") as MockClientManager, patch(
        "model_platform.infrastructure.mlflow_handler_adapter.MLFlowModelRegistryAdapter"
    ) as MockRegistryAdapter:
        mock_client_manager = MockClientManager.return_value
        mock_registry_adapter = MockRegistryAdapter.return_value

        mock_client_manager.initialize.return_value = None
        mock_registry_adapter.mlflow_client_manager = mock_client_manager

        yield mock_registry_adapter, mock_client_manager


@pytest.mark.asyncio
async def test_connect_creates_new_entry(mock_mlflow_client):
    registry_mock, _ = mock_mlflow_client

    handler = MLFlowHandlerAdapter()
    await asyncio.sleep(0.1)
    handler.get_registry_adapter("test", tracking_uri="http://127.0.0.1:5000")

    assert "test" in handler.client_pool
    assert isinstance(handler.client_pool["test"]["timestamp"], int)


@pytest.mark.asyncio
async def test_connect_reuses_existing_connection(mock_mlflow_client):
    registry_mock, _ = mock_mlflow_client

    handler = MLFlowHandlerAdapter()
    handler.client_pool["test"] = {"registry": registry_mock, "timestamp": int(time.time())}

    handler.get_registry_adapter(project_name="test", tracking_uri="http://127.0.0.1:5000")

    assert handler.client_pool["test"]["registry"] is registry_mock


@pytest.mark.asyncio
async def test_clean_client_pool_removes_expired_entries(mock_mlflow_client):
    registry_mock, client_manager_mock = mock_mlflow_client

    handler = MLFlowHandlerAdapter()
    handler.client_pool = {
        "valid_project": {"registry": registry_mock, "timestamp": int(time.time())},
        "expired_project": {"registry": registry_mock, "timestamp": int(time.time()) - 100},  # Expiré
    }

    handler.clean_client_pool(ttl_in_seconds=50)

    assert "valid_project" in handler.client_pool
    assert "expired_project" not in handler.client_pool
    client_manager_mock.close.assert_called_once()


@pytest.mark.asyncio
async def test_clean_client_pool_keeps_valid_entries(mock_mlflow_client):
    registry_mock, client_manager_mock = mock_mlflow_client

    handler = MLFlowHandlerAdapter()
    handler.client_pool = {"valid_project": {"registry": registry_mock, "timestamp": int(time.time()) - 10}}

    handler.clean_client_pool(ttl_in_seconds=50)

    assert "valid_project" in handler.client_pool
    client_manager_mock.close.assert_not_called()
