# Philippe Stepniewski
from unittest.mock import MagicMock

import pytest

from backend.domain.use_cases.model_info_usecases import sync_model_infos_for_project
from backend.infrastructure.model_info_sqlite_db_handler import ModelInfoAlreadyExistError


@pytest.fixture
def registry():
    mock = MagicMock()
    mock.list_all_models.return_value = [
        {"name": "model_a"},
        {"name": "model_b"},
    ]
    mock.list_model_versions.side_effect = lambda name: (
        [{"version": "1"}, {"version": "2"}] if name == "model_a" else [{"version": "1"}]
    )
    mock.get_model_card.return_value = None
    mock.get_model_governance_information.return_value = {"tags": {}}
    return mock


@pytest.fixture
def model_info_db_handler():
    return MagicMock()


def test_sync_calls_add_for_each_version(registry, model_info_db_handler):
    sync_model_infos_for_project("my_project", registry, model_info_db_handler)

    assert model_info_db_handler.add_model_info.call_count == 3  # 2 for model_a + 1 for model_b


def test_sync_passes_correct_model_info(registry, model_info_db_handler):
    sync_model_infos_for_project("my_project", registry, model_info_db_handler)

    calls = model_info_db_handler.add_model_info.call_args_list
    added = {(c.args[0].model_name, c.args[0].model_version, c.args[0].project_name) for c in calls}
    assert ("model_a", "1", "my_project") in added
    assert ("model_a", "2", "my_project") in added
    assert ("model_b", "1", "my_project") in added


def test_sync_stores_model_card_when_present(registry, model_info_db_handler):
    registry.get_model_card.return_value = "# My Model Card"

    sync_model_infos_for_project("my_project", registry, model_info_db_handler)

    calls = model_info_db_handler.add_model_info.call_args_list
    for c in calls:
        assert c.args[0].model_card == "# My Model Card"


def test_sync_model_card_is_none_when_absent(registry, model_info_db_handler):
    registry.get_model_card.return_value = None

    sync_model_infos_for_project("my_project", registry, model_info_db_handler)

    calls = model_info_db_handler.add_model_info.call_args_list
    for c in calls:
        assert c.args[0].model_card is None


def test_sync_updates_model_card_when_already_exists_and_card_present(registry, model_info_db_handler):
    registry.get_model_card.return_value = "# My Model Card"
    model_info_db_handler.add_model_info.side_effect = ModelInfoAlreadyExistError(
        message="already exists",
        model_name="model_a",
        model_version="1",
        project_name="my_project",
    )

    sync_model_infos_for_project("my_project", registry, model_info_db_handler)

    assert model_info_db_handler.update_model_card.call_count == 3
    model_info_db_handler.update_model_card.assert_any_call(
        model_name="model_a",
        model_version="1",
        project_name="my_project",
        model_card="# My Model Card",
    )


def test_sync_does_not_update_model_card_when_already_exists_and_card_absent(registry, model_info_db_handler):
    registry.get_model_card.return_value = None
    model_info_db_handler.add_model_info.side_effect = ModelInfoAlreadyExistError(
        message="already exists",
        model_name="model_a",
        model_version="1",
        project_name="my_project",
    )

    sync_model_infos_for_project("my_project", registry, model_info_db_handler)

    model_info_db_handler.update_model_card.assert_not_called()


def test_sync_with_empty_registry(model_info_db_handler):
    empty_registry = MagicMock()
    empty_registry.list_all_models.return_value = []

    sync_model_infos_for_project("my_project", empty_registry, model_info_db_handler)

    model_info_db_handler.add_model_info.assert_not_called()
