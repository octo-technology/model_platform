import pytest

from backend.domain.entities.model_info import ModelInfo
from backend.infrastructure.model_info_sqlite_db_handler import (
    ModelInfoAlreadyExistError,
    ModelInfoDoesntExistError,
    ModelInfoSQLiteDBHandler,
)


@pytest.fixture
def handler(tmp_path):
    return ModelInfoSQLiteDBHandler(db_path=str(tmp_path / "test.db"))


def test_add_model_info(handler):
    model_info = ModelInfo(model_name="my_model", model_version="1", project_name="proj_a", risk_level="high")
    result = handler.add_model_info(model_info)
    assert result is True


def test_add_model_info_duplicate_raises(handler):
    model_info = ModelInfo(model_name="my_model", model_version="1", project_name="proj_a")
    handler.add_model_info(model_info)
    with pytest.raises(ModelInfoAlreadyExistError):
        handler.add_model_info(model_info)


def test_get_model_info(handler):
    model_info = ModelInfo(
        model_name="my_model", model_version="1", project_name="proj_a", model_card="# Card", risk_level="minimal"
    )
    handler.add_model_info(model_info)
    retrieved = handler.get_model_info(model_name="my_model", model_version="1", project_name="proj_a")
    assert retrieved.model_name == "my_model"
    assert retrieved.model_version == "1"
    assert retrieved.project_name == "proj_a"
    assert retrieved.model_card == "# Card"
    assert retrieved.risk_level == "minimal"


def test_get_model_info_not_found_raises(handler):
    with pytest.raises(ModelInfoDoesntExistError):
        handler.get_model_info(model_name="unknown", model_version="1", project_name="proj_a")


def test_list_model_infos_for_project(handler):
    handler.add_model_info(ModelInfo(model_name="model_a", model_version="1", project_name="proj_x"))
    handler.add_model_info(ModelInfo(model_name="model_b", model_version="2", project_name="proj_x"))
    handler.add_model_info(ModelInfo(model_name="model_c", model_version="1", project_name="proj_y"))
    results = handler.list_model_infos_for_project(project_name="proj_x")
    assert len(results) == 2
    names = {m.model_name for m in results}
    assert names == {"model_a", "model_b"}


def test_update_model_card(handler):
    model_info = ModelInfo(model_name="my_model", model_version="1", project_name="proj_a", risk_level="high")
    handler.add_model_info(model_info)
    handler.update_model_card(
        model_name="my_model", model_version="1", project_name="proj_a", model_card="# Updated card"
    )
    retrieved = handler.get_model_info(model_name="my_model", model_version="1", project_name="proj_a")
    assert retrieved.model_card == "# Updated card"
    assert retrieved.risk_level == "high"


def test_delete_model_info(handler):
    model_info = ModelInfo(model_name="my_model", model_version="1", project_name="proj_a")
    handler.add_model_info(model_info)
    handler.delete_model_info(model_name="my_model", model_version="1", project_name="proj_a")
    with pytest.raises(ModelInfoDoesntExistError):
        handler.get_model_info(model_name="my_model", model_version="1", project_name="proj_a")


def test_search_model_infos_by_model_card(handler):
    handler.add_model_info(
        ModelInfo(model_name="model_a", model_version="1", project_name="proj_x", model_card="image classification")
    )
    handler.add_model_info(
        ModelInfo(model_name="model_b", model_version="1", project_name="proj_x", model_card="text generation")
    )
    results = handler.search_model_infos(query="classification")
    assert len(results) == 1
    assert results[0].model_name == "model_a"


def test_search_model_infos_by_risk_level(handler):
    handler.add_model_info(ModelInfo(model_name="model_a", model_version="1", project_name="proj_x", risk_level="high"))
    handler.add_model_info(
        ModelInfo(model_name="model_b", model_version="1", project_name="proj_x", risk_level="minimal")
    )
    results = handler.search_model_infos(query="high")
    assert len(results) == 1
    assert results[0].model_name == "model_a"


def test_search_model_infos_scoped_to_project(handler):
    handler.add_model_info(
        ModelInfo(model_name="model_a", model_version="1", project_name="proj_x", model_card="deep learning")
    )
    handler.add_model_info(
        ModelInfo(model_name="model_b", model_version="1", project_name="proj_y", model_card="deep learning")
    )
    results = handler.search_model_infos(query="deep", project_name="proj_x")
    assert len(results) == 1
    assert results[0].project_name == "proj_x"


def test_search_model_infos_no_results(handler):
    handler.add_model_info(
        ModelInfo(model_name="model_a", model_version="1", project_name="proj_x", model_card="image classification")
    )
    results = handler.search_model_infos(query="nonexistent_term_xyz")
    assert results == []
