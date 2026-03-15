# Philippe Stepniewski
import pytest

from backend.domain.entities.model_info import ModelInfo
from backend.domain.use_cases.compliance_usecases import (
    COMPLIANCE_COMPLIANT,
    COMPLIANCE_NON_COMPLIANT,
    COMPLIANCE_NOT_EVALUATED,
    COMPLIANCE_PARTIALLY_COMPLIANT,
    check_deployment_gate,
    evaluate_deterministic_compliance,
    extract_llm_compliance_from_review,
)


def _make_model_info(**kwargs):
    defaults = {
        "model_name": "test_model",
        "model_version": "1",
        "project_name": "test_project",
    }
    defaults.update(kwargs)
    return ModelInfo(**defaults)


def _make_governance(tags=None, params=None, metrics=None):
    return {
        "tags": tags or {},
        "params": params or {},
        "metrics": metrics or {},
    }


class TestEvaluateDeterministicCompliance:
    def test_unacceptable_risk_returns_non_compliant(self):
        model_info = _make_model_info(risk_level="unacceptable", model_card="some card")
        governance = _make_governance(
            tags={"mlflow.user": "alice"},
            metrics={"accuracy": 0.9},
            params={"lr": 0.01},
        )
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_NON_COMPLIANT

    def test_no_risk_level_returns_non_compliant(self):
        model_info = _make_model_info(risk_level=None, model_card="some card")
        governance = _make_governance(tags={"mlflow.user": "alice"}, metrics={"accuracy": 0.9})
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_NON_COMPLIANT

    def test_no_model_card_returns_non_compliant(self):
        model_info = _make_model_info(risk_level="high", model_card=None)
        governance = _make_governance(tags={"mlflow.user": "alice"}, metrics={"accuracy": 0.9})
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_NON_COMPLIANT

    def test_mlflow_note_as_model_card(self):
        model_info = _make_model_info(risk_level="high", model_card=None)
        governance = _make_governance(
            tags={"mlflow.user": "alice", "mlflow.note.content": "A note"},
            metrics={"accuracy": 0.9},
            params={"lr": 0.01},
        )
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_COMPLIANT

    def test_no_metrics_returns_non_compliant(self):
        model_info = _make_model_info(risk_level="high", model_card="card")
        governance = _make_governance(tags={"mlflow.user": "alice"}, metrics={})
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_NON_COMPLIANT

    def test_no_author_returns_non_compliant(self):
        model_info = _make_model_info(risk_level="high", model_card="card")
        governance = _make_governance(tags={}, metrics={"accuracy": 0.9})
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_NON_COMPLIANT

    def test_all_mandatory_no_recommended_returns_partially_compliant(self):
        model_info = _make_model_info(risk_level="high", model_card="card")
        governance = _make_governance(tags={"mlflow.user": "alice"}, metrics={"accuracy": 0.9}, params={})
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_PARTIALLY_COMPLIANT

    def test_all_mandatory_with_params_returns_compliant(self):
        model_info = _make_model_info(risk_level="high", model_card="card")
        governance = _make_governance(
            tags={"mlflow.user": "alice"},
            metrics={"accuracy": 0.9},
            params={"lr": 0.01},
        )
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_COMPLIANT

    def test_all_mandatory_with_signature_returns_compliant(self):
        import json

        model_info = _make_model_info(risk_level="limited", model_card="card")
        history = json.dumps([{"signature": {"inputs": "col1", "outputs": "col2"}}])
        governance = _make_governance(
            tags={"mlflow.user": "bob", "mlflow.log-model.history": history},
            metrics={"f1": 0.85},
            params={},
        )
        assert evaluate_deterministic_compliance(model_info, governance) == COMPLIANCE_COMPLIANT


class TestExtractLlmCompliance:
    def test_none_review(self):
        assert extract_llm_compliance_from_review(None) == COMPLIANCE_NOT_EVALUATED

    def test_empty_review(self):
        assert extract_llm_compliance_from_review("") == COMPLIANCE_NOT_EVALUATED

    def test_no_score_in_review(self):
        assert extract_llm_compliance_from_review("Some review text without score") == COMPLIANCE_NOT_EVALUATED

    def test_score_7_compliant(self):
        review = "## Score de complétude — 7/10\nGood model."
        assert extract_llm_compliance_from_review(review) == COMPLIANCE_COMPLIANT

    def test_score_10_compliant(self):
        review = "Score de complétude: 10/10"
        assert extract_llm_compliance_from_review(review) == COMPLIANCE_COMPLIANT

    def test_score_5_partially(self):
        review = "Score de complétude — 5/10"
        assert extract_llm_compliance_from_review(review) == COMPLIANCE_PARTIALLY_COMPLIANT

    def test_score_4_partially(self):
        review = "Score de complétude — 4/10"
        assert extract_llm_compliance_from_review(review) == COMPLIANCE_PARTIALLY_COMPLIANT

    def test_score_3_non_compliant(self):
        review = "Score de complétude — 3/10"
        assert extract_llm_compliance_from_review(review) == COMPLIANCE_NON_COMPLIANT

    def test_score_0_non_compliant(self):
        review = "Score de complétude — 0/10"
        assert extract_llm_compliance_from_review(review) == COMPLIANCE_NON_COMPLIANT


class FakePlatformConfigHandler:
    def __init__(self, data=None):
        self._data = data or {}

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value):
        self._data[key] = value

    def delete(self, key):
        self._data.pop(key, None)


class TestCheckDeploymentGate:
    def test_disabled_policy_always_allows(self):
        model_info = _make_model_info(deterministic_compliance="non_compliant", llm_compliance="non_compliant")
        config = FakePlatformConfigHandler({"DEPLOYMENT_GATE_POLICY": "disabled"})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is True

    def test_permissive_both_not_evaluated_blocks(self):
        model_info = _make_model_info(deterministic_compliance="not_evaluated", llm_compliance="not_evaluated")
        config = FakePlatformConfigHandler({"DEPLOYMENT_GATE_POLICY": "permissive"})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is False

    def test_permissive_one_compliant_allows(self):
        model_info = _make_model_info(deterministic_compliance="compliant", llm_compliance="not_evaluated")
        config = FakePlatformConfigHandler({"DEPLOYMENT_GATE_POLICY": "permissive"})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is True

    def test_permissive_one_partially_allows(self):
        model_info = _make_model_info(deterministic_compliance="non_compliant", llm_compliance="partially_compliant")
        config = FakePlatformConfigHandler({"DEPLOYMENT_GATE_POLICY": "permissive"})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is True

    def test_strict_both_compliant_allows(self):
        model_info = _make_model_info(deterministic_compliance="compliant", llm_compliance="compliant")
        config = FakePlatformConfigHandler({"DEPLOYMENT_GATE_POLICY": "strict"})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is True

    def test_strict_one_missing_blocks(self):
        model_info = _make_model_info(deterministic_compliance="compliant", llm_compliance="not_evaluated")
        config = FakePlatformConfigHandler({"DEPLOYMENT_GATE_POLICY": "strict"})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is False

    def test_strict_one_non_compliant_blocks(self):
        model_info = _make_model_info(deterministic_compliance="non_compliant", llm_compliance="compliant")
        config = FakePlatformConfigHandler({"DEPLOYMENT_GATE_POLICY": "strict"})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is False

    def test_default_policy_is_permissive(self):
        model_info = _make_model_info(deterministic_compliance="compliant", llm_compliance="not_evaluated")
        config = FakePlatformConfigHandler({})
        allowed, reason = check_deployment_gate(model_info, config)
        assert allowed is True
