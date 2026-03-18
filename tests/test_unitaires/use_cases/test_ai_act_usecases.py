# Philippe Stepniewski
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.domain.entities.model_info import ModelInfo
from backend.domain.use_cases.ai_act_usecases import (
    _extract_model_type,
    _extract_signature,
    _format_created_date,
    _metrics_table,
    _params_table,
    _risk_level_checkboxes,
    generate_ai_act_card,
)


def _make_tags(**overrides):
    tags = {}
    tags.update(overrides)
    return tags


def _make_history_json(flavors=None, signature=None, utc_time_created=None):
    entry = {}
    if flavors is not None:
        entry["flavors"] = flavors
    if signature is not None:
        entry["signature"] = signature
    if utc_time_created is not None:
        entry["utc_time_created"] = utc_time_created
    return json.dumps([entry])


class TestRiskLevelCheckboxes:
    def test_high_risk(self):
        result = _risk_level_checkboxes("high")
        assert "[x] **Risque élevé" in result
        assert "[ ] **Risque inacceptable" in result
        assert "[ ] **Risque limité" in result
        assert "[ ] **Risque minimal" in result

    def test_unacceptable_risk(self):
        result = _risk_level_checkboxes("unacceptable")
        assert "[x] **Risque inacceptable" in result
        assert "[ ] **Risque élevé" in result

    def test_minimal_risk(self):
        result = _risk_level_checkboxes("minimal")
        assert "[x] **Risque minimal" in result
        assert "[ ] **Risque élevé" in result

    def test_limited_risk(self):
        result = _risk_level_checkboxes("limited")
        assert "[x] **Risque limité" in result
        assert "[ ] **Risque élevé" in result

    def test_none_risk(self):
        result = _risk_level_checkboxes(None)
        assert "[x]" not in result
        assert result.count("[ ]") == 4


class TestParamsTable:
    def test_empty_params(self):
        assert _params_table({}) == "*Aucun hyperparamètre enregistré.*"

    def test_single_param(self):
        result = _params_table({"lr": "0.01"})
        assert "| Paramètre | Valeur |" in result
        assert "| `lr` | `0.01` |" in result

    def test_multiple_params(self):
        result = _params_table({"lr": "0.01", "epochs": "10"})
        assert "| `lr` | `0.01` |" in result
        assert "| `epochs` | `10` |" in result


class TestMetricsTable:
    def test_empty_metrics(self):
        assert _metrics_table({}) == "*Aucune métrique enregistrée.*"

    def test_single_metric(self):
        result = _metrics_table({"accuracy": "0.95"})
        assert "Seuil d'acceptation" in result
        assert "| `accuracy` | `0.95` | *N/A* |" in result

    def test_multiple_metrics(self):
        result = _metrics_table({"accuracy": "0.95", "f1": "0.9"})
        assert "| `accuracy` | `0.95` | *N/A* |" in result
        assert "| `f1` | `0.9` | *N/A* |" in result


class TestFormatCreatedDate:
    def test_valid_tags_returns_utc_time_created(self):
        history = _make_history_json(utc_time_created="2026-01-15 10:30:00 UTC")
        tags = _make_tags(**{"mlflow.log-model.history": history})
        assert _format_created_date(tags) == "2026-01-15 10:30:00 UTC"

    def test_empty_tags_returns_today(self):
        tags = {}
        result = _format_created_date(tags)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert today in result

    def test_malformed_json_returns_fallback(self):
        tags = _make_tags(**{"mlflow.log-model.history": "not valid json"})
        result = _format_created_date(tags)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert today in result


class TestExtractModelType:
    def test_sklearn_and_python_function(self):
        history = _make_history_json(flavors={"sklearn": {}, "python_function": {}})
        tags = _make_tags(**{"mlflow.log-model.history": history})
        assert _extract_model_type(tags) == "sklearn"

    def test_multiple_non_pyfunc_flavors(self):
        history = _make_history_json(flavors={"sklearn": {}, "xgboost": {}, "python_function": {}})
        tags = _make_tags(**{"mlflow.log-model.history": history})
        result = _extract_model_type(tags)
        assert "sklearn" in result
        assert "xgboost" in result

    def test_only_python_function(self):
        history = _make_history_json(flavors={"python_function": {}})
        tags = _make_tags(**{"mlflow.log-model.history": history})
        assert _extract_model_type(tags) == "*à compléter*"

    def test_no_history(self):
        tags = {}
        assert _extract_model_type(tags) == "*à compléter*"


class TestExtractSignature:
    def test_valid_signature(self):
        history = _make_history_json(signature={"inputs": "[col1]", "outputs": "[col2]"})
        tags = _make_tags(**{"mlflow.log-model.history": history})
        inputs, outputs = _extract_signature(tags)
        assert inputs == "[col1]"
        assert outputs == "[col2]"

    def test_no_signature(self):
        history = _make_history_json(flavors={"sklearn": {}})
        tags = _make_tags(**{"mlflow.log-model.history": history})
        inputs, outputs = _extract_signature(tags)
        assert inputs == "*à compléter*"
        assert outputs == "*à compléter*"

    def test_no_history(self):
        tags = {}
        inputs, outputs = _extract_signature(tags)
        assert inputs == "*à compléter*"
        assert outputs == "*à compléter*"


class TestGenerateAiActCard:
    @pytest.fixture
    def registry(self):
        mock = MagicMock()
        mock.get_model_governance_information.return_value = {
            "tags": {
                "mlflow.user": "alice",
                "mlflow.runName": "run_1",
                "mlflow.log-model.history": _make_history_json(
                    flavors={"sklearn": {}, "python_function": {}},
                    signature={"inputs": "[col1]", "outputs": "[col2]"},
                    utc_time_created="2026-01-15 10:00 UTC",
                ),
            },
            "params": {"lr": "0.01"},
            "metrics": {"accuracy": "0.95"},
            "run_id": "abc123",
        }
        return mock

    @pytest.fixture
    def db_handler(self):
        mock = MagicMock()
        mock.get_model_info.return_value = ModelInfo(
            model_name="my_model",
            model_version="1",
            project_name="my_project",
            risk_level="high",
            model_card="My model description",
        )
        return mock

    @patch("backend.domain.use_cases.ai_act_usecases._load_template")
    def test_complete_data_renders_values(self, mock_template, registry, db_handler):
        mock_template.return_value = (
            "name={model_name} version={version} project={project_name} "
            "run_id={run_id} run_name={run_name} date={created_date} "
            "user={user} risk={risk_level_checkboxes} desc={description} "
            "type={model_type} in={sig_inputs} out={sig_outputs} "
            "params={params_table} metrics={metrics_table} now={now_str}"
        )
        result = generate_ai_act_card(registry, db_handler, "my_project", "my_model", "1")
        assert "name=my_model" in result
        assert "version=1" in result
        assert "user=alice" in result
        assert "desc=My model description" in result
        assert "type=sklearn" in result

    @patch("backend.domain.use_cases.ai_act_usecases._load_template")
    def test_no_model_info_uses_fallbacks(self, mock_template, registry):
        db_handler = MagicMock()
        db_handler.get_model_info.return_value = None
        registry.get_model_governance_information.return_value = {
            "tags": {"mlflow.note.content": "A note from MLflow"},
            "params": {},
            "metrics": {},
            "run_id": "xyz",
        }
        mock_template.return_value = "desc={description} risk={risk_level_checkboxes}"
        result = generate_ai_act_card(registry, db_handler, "proj", "model", "1")
        assert "desc=A note from MLflow" in result
        assert "[x]" not in result

    @patch("backend.domain.use_cases.ai_act_usecases._load_template")
    def test_fallback_mlflow_note_when_no_model_card(self, mock_template, registry):
        db_handler = MagicMock()
        db_handler.get_model_info.return_value = ModelInfo(
            model_name="m", model_version="1", project_name="p", risk_level="high", model_card=None
        )
        registry.get_model_governance_information.return_value = {
            "tags": {"mlflow.note.content": "Fallback note"},
            "params": {},
            "metrics": {},
            "run_id": "xyz",
        }
        mock_template.return_value = "desc={description}"
        result = generate_ai_act_card(registry, db_handler, "p", "m", "1")
        assert "desc=Fallback note" in result
