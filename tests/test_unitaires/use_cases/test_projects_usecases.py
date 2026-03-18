# Philippe Stepniewski
import os
from unittest.mock import MagicMock, patch

import pytest

# Set required env var before importing the module that needs it
os.environ.setdefault("PATH_LOG_EVENTS", "/tmp/test_log_events")

from backend.domain.entities.project import Project
from backend.domain.use_cases.projects_usecases import add_project, remove_project, update_project_batch_enabled


@pytest.fixture
def mock_project_db_handler():
    handler = MagicMock()
    handler.add_project.return_value = True
    handler.remove_project.return_value = True
    handler.update_batch_enabled.return_value = True
    return handler


@pytest.fixture
def mock_object_storage():
    return MagicMock()


@patch("backend.domain.use_cases.projects_usecases.deploy_registry")
def test_add_project_with_batch_enabled_creates_storage_space(
    mock_deploy_registry, mock_project_db_handler, mock_object_storage
):
    project = Project(name="test-project", owner="owner", scope="scope", data_perimeter="perimeter", batch_enabled=True)

    add_project(mock_project_db_handler, project, mock_object_storage)

    mock_object_storage.ensure_project_space.assert_called_once_with("test-project")
    mock_project_db_handler.add_project.assert_called_once_with(project)


@patch("backend.domain.use_cases.projects_usecases.deploy_registry")
def test_add_project_without_batch_does_not_create_storage_space(
    mock_deploy_registry, mock_project_db_handler, mock_object_storage
):
    project = Project(
        name="test-project", owner="owner", scope="scope", data_perimeter="perimeter", batch_enabled=False
    )

    add_project(mock_project_db_handler, project, mock_object_storage)

    mock_object_storage.ensure_project_space.assert_not_called()
    mock_project_db_handler.add_project.assert_called_once_with(project)


@patch("backend.domain.use_cases.projects_usecases._remove_project_namespace")
def test_remove_project_cleans_up_storage(mock_remove_ns, mock_project_db_handler, mock_object_storage):
    remove_project(mock_project_db_handler, "test-project", mock_object_storage)

    mock_object_storage.remove_project_space.assert_called_once_with("test-project")
    mock_project_db_handler.remove_project.assert_called_once_with("test-project")


@patch("backend.domain.use_cases.projects_usecases._remove_project_namespace")
def test_remove_project_continues_if_storage_cleanup_fails(
    mock_remove_ns, mock_project_db_handler, mock_object_storage
):
    mock_object_storage.remove_project_space.side_effect = Exception("Storage error")

    result = remove_project(mock_project_db_handler, "test-project", mock_object_storage)

    assert result is True
    mock_project_db_handler.remove_project.assert_called_once_with("test-project")


def test_update_batch_enabled_to_true_creates_space(mock_project_db_handler, mock_object_storage):
    update_project_batch_enabled(mock_project_db_handler, "test-project", True, mock_object_storage)

    mock_object_storage.ensure_project_space.assert_called_once_with("test-project")
    mock_project_db_handler.update_batch_enabled.assert_called_once_with("test-project", True)


def test_update_batch_enabled_to_false_removes_space(mock_project_db_handler, mock_object_storage):
    update_project_batch_enabled(mock_project_db_handler, "test-project", False, mock_object_storage)

    mock_object_storage.remove_project_space.assert_called_once_with("test-project")
    mock_project_db_handler.update_batch_enabled.assert_called_once_with("test-project", False)
