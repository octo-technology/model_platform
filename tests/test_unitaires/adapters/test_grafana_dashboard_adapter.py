from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.rest import ApiException

from backend.infrastructure.grafana_dashboard_adapter import GrafanaDashboardAdapter


@pytest.fixture
def mock_k8s_config():
    with patch("backend.infrastructure.grafana_dashboard_adapter.config") as mock_config:
        yield mock_config


@pytest.fixture
def mock_k8s_client():
    with patch("backend.infrastructure.grafana_dashboard_adapter.client") as mock_client:
        mock_v1 = MagicMock()
        mock_client.CoreV1Api.return_value = mock_v1
        yield mock_v1


@pytest.fixture
def adapter(mock_k8s_config, mock_k8s_client):
    return GrafanaDashboardAdapter()


def test_create_dashboard_creates_configmap(adapter, mock_k8s_client):
    mock_k8s_client.read_namespaced_config_map.side_effect = ApiException(status=404)

    result = adapter.create_dashboard(
        project_name="test-project",
        model_name="test-model",
        version="v1",
        service_name="test-service",
        dashboard_uid="test-project-test-model-v1-abc123",
    )

    assert result is True
    mock_k8s_client.create_namespaced_config_map.assert_called_once()

    call_args = mock_k8s_client.create_namespaced_config_map.call_args
    assert call_args[1]["namespace"] == "monitoring"


def test_create_dashboard_updates_existing_configmap(adapter, mock_k8s_client):
    mock_k8s_client.read_namespaced_config_map.return_value = MagicMock()

    result = adapter.create_dashboard(
        project_name="test-project",
        model_name="test-model",
        version="v1",
        service_name="test-service",
        dashboard_uid="test-project-test-model-v1-abc123",
    )

    assert result is True
    mock_k8s_client.replace_namespaced_config_map.assert_called_once()
    mock_k8s_client.create_namespaced_config_map.assert_not_called()


def test_create_dashboard_sets_correct_labels(adapter, mock_k8s_client):
    mock_k8s_client.read_namespaced_config_map.side_effect = ApiException(status=404)

    adapter.create_dashboard(
        project_name="test-project",
        model_name="test-model",
        version="v1",
        service_name="test-service",
        dashboard_uid="test-project-test-model-v1-abc123",
    )

    call_args = mock_k8s_client.create_namespaced_config_map.call_args
    configmap = call_args[1]["body"]
    assert configmap.metadata.labels["grafana_dashboard"] == "1"


def test_delete_dashboard_removes_configmap(adapter, mock_k8s_client):
    result = adapter.delete_dashboard(
        project_name="test-project",
        model_name="test-model",
        version="v1",
        dashboard_uid="test-project-test-model-v1-abc123",
    )

    assert result is True
    mock_k8s_client.delete_namespaced_config_map.assert_called_once()


def test_delete_dashboard_handles_not_found(adapter, mock_k8s_client):
    mock_k8s_client.delete_namespaced_config_map.side_effect = ApiException(status=404)

    result = adapter.delete_dashboard(
        project_name="test-project",
        model_name="test-model",
        version="v1",
        dashboard_uid="test-project-test-model-v1-abc123",
    )

    assert result is True


def test_delete_dashboard_handles_error(adapter, mock_k8s_client):
    mock_k8s_client.delete_namespaced_config_map.side_effect = ApiException(status=500)

    result = adapter.delete_dashboard(
        project_name="test-project",
        model_name="test-model",
        version="v1",
        dashboard_uid="test-project-test-model-v1-abc123",
    )

    assert result is False


def test_generate_dashboard_uid_basic(adapter):
    """Test basic UID generation."""
    uid = adapter.generate_dashboard_uid(
        project_name="vio",
        model_name="marker_quality_control",
        version="1",
    )

    assert uid is not None
    assert len(uid) > 0
    assert len(uid) <= 40


def test_generate_dashboard_uid_respects_40_char_limit(adapter):
    """Test that UID generation respects Grafana's 40 character limit even with long names."""
    uid = adapter.generate_dashboard_uid(
        project_name="my-very-long-project-name",
        model_name="super-complex-model-with-many-features",
        version="123",
    )

    assert len(uid) <= 40


def test_generate_dashboard_uid_consistency(adapter):
    """Test that the same inputs always produce the same UID."""
    uid1 = adapter.generate_dashboard_uid(
        project_name="test-project",
        model_name="test-model",
        version="v1",
    )
    uid2 = adapter.generate_dashboard_uid(
        project_name="test-project",
        model_name="test-model",
        version="v1",
    )

    assert uid1 == uid2


def test_generate_dashboard_uid_sanitizes_special_chars(adapter):
    """Test that special characters are sanitized."""
    uid = adapter.generate_dashboard_uid(
        project_name="Test_Project",
        model_name="My Model",
        version="1.0",
    )

    # Should only contain lowercase alphanumeric and dashes
    assert uid == uid.lower()
    assert "_" not in uid
    assert " " not in uid
    assert "." not in uid
