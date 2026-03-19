# Philippe Stepniewski
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("PATH_LOG_EVENTS", "/tmp/test_log_events")

from backend.domain.entities.batch_prediction import BatchPrediction, BatchPredictionStatus
from backend.domain.entities.project import Project
from backend.domain.use_cases.batch_predict import (
    delete_batch_prediction,
    download_batch_result,
    get_batch_prediction_status,
    list_batch_predictions,
    submit_batch_prediction,
)


@pytest.fixture
def mock_batch_handler():
    return MagicMock()


@pytest.fixture
def mock_object_storage():
    return MagicMock()


@pytest.fixture
def mock_project_db_handler():
    handler = MagicMock()
    handler.get_project.return_value = Project(
        name="test-project", owner="owner", scope="scope", data_perimeter="perimeter", batch_enabled=True
    )
    return handler


@pytest.fixture
def mock_registry():
    return MagicMock()


@pytest.fixture
def sample_batch_prediction():
    from datetime import datetime, timezone

    return BatchPrediction(
        job_id="abc12345",
        project_name="test-project",
        model_name="my-model",
        model_version="1",
        status=BatchPredictionStatus.PENDING,
        input_path="test-project/my-model/1/abc12345/input.csv",
        output_path="test-project/my-model/1/abc12345/predictions-abc12345.csv",
        created_at=datetime.now(timezone.utc),
    )


def test_submit_uploads_file_and_creates_job(
    mock_batch_handler, mock_object_storage, mock_project_db_handler, sample_batch_prediction
):
    mock_batch_handler.create_batch_job.return_value = sample_batch_prediction

    result = submit_batch_prediction(
        project_name="test-project",
        model_name="my-model",
        version="1",
        file_content=b"col1,col2\n1,2\n3,4",
        job_id="abc12345",
        object_storage=mock_object_storage,
        batch_handler=mock_batch_handler,
        project_db_handler=mock_project_db_handler,
    )

    mock_object_storage.upload_file.assert_called_once()
    mock_batch_handler.create_batch_job.assert_called_once()
    assert result["project_name"] == "test-project"
    assert result["model_name"] == "my-model"


def test_submit_fails_if_batch_not_enabled(mock_batch_handler, mock_object_storage):
    project_db = MagicMock()
    project_db.get_project.return_value = Project(
        name="test-project", owner="owner", scope="scope", data_perimeter="perimeter", batch_enabled=False
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        submit_batch_prediction(
            project_name="test-project",
            model_name="my-model",
            version="1",
            file_content=b"col1,col2\n1,2",
            job_id="abc12345",
            object_storage=mock_object_storage,
            batch_handler=mock_batch_handler,
            project_db_handler=project_db,
        )
    assert exc_info.value.status_code == 400


def test_get_status_delegates_to_handler(mock_batch_handler, sample_batch_prediction):
    mock_batch_handler.get_job_status.return_value = sample_batch_prediction

    result = get_batch_prediction_status("test-project", "abc12345", mock_batch_handler)

    mock_batch_handler.get_job_status.assert_called_once_with("test-project", "abc12345")
    assert result["job_id"] == "abc12345"
    assert result["status"] == "pending"


def test_list_delegates_to_handler(mock_batch_handler, sample_batch_prediction):
    mock_batch_handler.list_batch_jobs.return_value = [sample_batch_prediction]

    result = list_batch_predictions("test-project", mock_batch_handler)

    mock_batch_handler.list_batch_jobs.assert_called_once_with("test-project")
    assert len(result) == 1
    assert result[0]["job_id"] == "abc12345"


def test_download_returns_file_content(mock_batch_handler, mock_object_storage, sample_batch_prediction):
    mock_batch_handler.get_job_status.return_value = sample_batch_prediction
    mock_object_storage.download_file.return_value = b"prediction\n0.95\n0.32"

    result = download_batch_result("test-project", "abc12345", mock_batch_handler, mock_object_storage)

    mock_object_storage.download_file.assert_called_once_with(
        "test-project", "my-model/1/abc12345/predictions-abc12345.csv"
    )
    assert result == b"prediction\n0.95\n0.32"


def test_delete_cleans_up_job_and_storage(mock_batch_handler, mock_object_storage, sample_batch_prediction):
    mock_batch_handler.get_job_status.return_value = sample_batch_prediction
    mock_batch_handler.delete_batch_job.return_value = True
    mock_object_storage.list_files.return_value = [
        "my-model/1/abc12345/input.csv",
        "my-model/1/abc12345/predictions-abc12345.csv",
    ]

    result = delete_batch_prediction("test-project", "abc12345", mock_batch_handler, mock_object_storage)

    assert result is True
    mock_batch_handler.delete_batch_job.assert_called_once_with("test-project", "abc12345")
    assert mock_object_storage.delete_file.call_count == 2


@patch("backend.domain.use_cases.batch_predict.build_model_docker_image")
@patch("backend.domain.use_cases.batch_predict.check_docker_image_exists")
def test_submit_builds_image_if_not_exists(
    mock_check,
    mock_build,
    mock_batch_handler,
    mock_object_storage,
    mock_project_db_handler,
    mock_registry,
    sample_batch_prediction,
):
    mock_check.return_value = False
    mock_build.return_value = 1
    mock_batch_handler.create_batch_job.return_value = sample_batch_prediction

    submit_batch_prediction(
        project_name="test-project",
        model_name="my-model",
        version="1",
        file_content=b"col1,col2\n1,2",
        job_id="abc12345",
        object_storage=mock_object_storage,
        batch_handler=mock_batch_handler,
        project_db_handler=mock_project_db_handler,
        registry=mock_registry,
    )

    mock_check.assert_called_once()
    mock_build.assert_called_once_with(mock_registry, "test-project", "my-model", "1")


@patch("backend.domain.use_cases.batch_predict.build_model_docker_image")
@patch("backend.domain.use_cases.batch_predict.check_docker_image_exists")
def test_submit_skips_build_if_image_exists(
    mock_check,
    mock_build,
    mock_batch_handler,
    mock_object_storage,
    mock_project_db_handler,
    mock_registry,
    sample_batch_prediction,
):
    mock_check.return_value = True
    mock_batch_handler.create_batch_job.return_value = sample_batch_prediction

    submit_batch_prediction(
        project_name="test-project",
        model_name="my-model",
        version="1",
        file_content=b"col1,col2\n1,2",
        job_id="abc12345",
        object_storage=mock_object_storage,
        batch_handler=mock_batch_handler,
        project_db_handler=mock_project_db_handler,
        registry=mock_registry,
    )

    mock_check.assert_called_once()
    mock_build.assert_not_called()


@patch("backend.domain.use_cases.batch_predict.build_model_docker_image")
@patch("backend.domain.use_cases.batch_predict.check_docker_image_exists")
def test_submit_fails_if_build_fails(
    mock_check, mock_build, mock_batch_handler, mock_object_storage, mock_project_db_handler, mock_registry
):
    mock_check.return_value = False
    mock_build.return_value = 0

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        submit_batch_prediction(
            project_name="test-project",
            model_name="my-model",
            version="1",
            file_content=b"col1,col2\n1,2",
            job_id="abc12345",
            object_storage=mock_object_storage,
            batch_handler=mock_batch_handler,
            project_db_handler=mock_project_db_handler,
            registry=mock_registry,
        )

    assert exc_info.value.status_code == 500
    assert "Failed to build model image" in exc_info.value.detail
