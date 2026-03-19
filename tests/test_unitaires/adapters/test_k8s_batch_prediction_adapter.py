# Philippe Stepniewski
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("PATH_LOG_EVENTS", "/tmp/test_log_events")
os.environ.setdefault("MP_HOST_NAME", "localhost")
os.environ.setdefault("MP_DEPLOYMENT_PATH", "/deploy")
os.environ.setdefault("MP_DEPLOYMENT_PORT", "8000")
os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "minio_user")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "minio_password")


from backend.domain.entities.batch_prediction import BatchPredictionStatus


@pytest.fixture
def mock_k8s():
    with (
        patch("backend.infrastructure.k8s_deployment.config") as mock_config,
        patch("backend.infrastructure.k8s_deployment.client") as mock_base_client,
        patch("backend.infrastructure.k8s_batch_prediction_adapter.client") as mock_client,
    ):
        mock_config.load_kube_config.return_value = None
        mock_base_client.CoreV1Api.return_value = MagicMock()
        mock_base_client.AppsV1Api.return_value = MagicMock()
        mock_base_client.NetworkingV1Api.return_value = MagicMock()
        mock_batch_api = MagicMock()
        mock_client.BatchV1Api.return_value = mock_batch_api
        mock_client.V1Job = MagicMock()
        mock_client.V1ObjectMeta = MagicMock()
        mock_client.V1JobSpec = MagicMock()
        mock_client.V1PodTemplateSpec = MagicMock()
        mock_client.V1PodSpec = MagicMock()
        mock_client.V1Container = MagicMock()
        mock_client.V1EnvVar = MagicMock()
        mock_client.V1DeleteOptions = MagicMock()

        yield mock_batch_api, mock_client


def test_create_batch_job(mock_k8s):
    mock_batch_api, mock_client = mock_k8s

    from backend.infrastructure.k8s_batch_prediction_adapter import K8sBatchPredictionAdapter

    adapter = K8sBatchPredictionAdapter()

    result = adapter.create_batch_job(
        project_name="test-project",
        model_name="my-model",
        model_version="1",
        input_path="test-project/my-model/1/abc/input.csv",
        output_path="test-project/my-model/1/abc/predictions-abc.csv",
        job_id="abc12345",
    )

    mock_batch_api.create_namespaced_job.assert_called_once()
    assert result.project_name == "test-project"
    assert result.model_name == "my-model"
    assert result.model_version == "1"
    assert result.status == BatchPredictionStatus.PENDING


def test_map_job_status_succeeded(mock_k8s):
    from backend.infrastructure.k8s_batch_prediction_adapter import K8sBatchPredictionAdapter

    adapter = K8sBatchPredictionAdapter()

    status = MagicMock()
    status.succeeded = 1
    status.failed = None
    status.active = None
    assert adapter._map_job_status(status) == BatchPredictionStatus.COMPLETED


def test_map_job_status_failed(mock_k8s):
    from backend.infrastructure.k8s_batch_prediction_adapter import K8sBatchPredictionAdapter

    adapter = K8sBatchPredictionAdapter()

    status = MagicMock()
    status.succeeded = None
    status.failed = 1
    status.active = None
    assert adapter._map_job_status(status) == BatchPredictionStatus.FAILED


def test_map_job_status_active(mock_k8s):
    from backend.infrastructure.k8s_batch_prediction_adapter import K8sBatchPredictionAdapter

    adapter = K8sBatchPredictionAdapter()

    status = MagicMock()
    status.succeeded = None
    status.failed = None
    status.active = 1
    assert adapter._map_job_status(status) == BatchPredictionStatus.RUNNING


def test_map_job_status_pending(mock_k8s):
    from backend.infrastructure.k8s_batch_prediction_adapter import K8sBatchPredictionAdapter

    adapter = K8sBatchPredictionAdapter()

    status = MagicMock()
    status.succeeded = None
    status.failed = None
    status.active = None
    assert adapter._map_job_status(status) == BatchPredictionStatus.PENDING


def test_delete_batch_job(mock_k8s):
    mock_batch_api, mock_client = mock_k8s

    from backend.infrastructure.k8s_batch_prediction_adapter import K8sBatchPredictionAdapter

    adapter = K8sBatchPredictionAdapter()

    result = adapter.delete_batch_job("test-project", "my-job-id")

    mock_batch_api.delete_namespaced_job.assert_called_once()
    call_kwargs = mock_batch_api.delete_namespaced_job.call_args
    assert call_kwargs[1]["name"] == "batch-my-job-id"
    assert call_kwargs[1]["namespace"] == "test-project"
    assert result is True
