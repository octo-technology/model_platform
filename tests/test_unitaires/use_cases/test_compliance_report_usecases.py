# Philippe Stepniewski
import os
from unittest.mock import MagicMock, patch

import pytest

from backend.domain.entities.model_info import ModelInfo
from backend.domain.entities.project import Project
from backend.domain.use_cases.compliance_report_usecases import (
    ModelVersionData,
    PlatformSummary,
    ProjectData,
    _build_pdf,
    _collect_platform_data,
    _compute_summary,
    generate_platform_compliance_report,
)


@pytest.fixture
def mock_project_db_handler():
    handler = MagicMock()
    handler.list_projects.return_value = [
        Project(name="project_a", owner="alice", scope="prod", data_perimeter="eu"),
        Project(name="project_b", owner="bob", scope="staging", data_perimeter="us"),
    ]
    return handler


@pytest.fixture
def mock_model_info_db_handler():
    handler = MagicMock()

    def list_model_infos(project_name):
        if project_name == "project_a":
            return [
                ModelInfo(
                    model_name="model_1",
                    model_version="1",
                    project_name="project_a",
                    risk_level="high",
                    deterministic_compliance="compliant",
                    llm_compliance="partially_compliant",
                    model_card="A good model card",
                    act_review="Score de completude : 7/10",
                ),
                ModelInfo(
                    model_name="model_1",
                    model_version="2",
                    project_name="project_a",
                    risk_level="minimal",
                    deterministic_compliance="not_evaluated",
                    llm_compliance="not_evaluated",
                ),
            ]
        return []

    handler.list_model_infos_for_project.side_effect = list_model_infos
    return handler


@pytest.fixture
def mock_registry_pool():
    pool = MagicMock()
    registry = MagicMock()
    registry.list_all_models.return_value = [{"name": "model_1"}]
    registry.list_model_versions.return_value = [{"version": "1"}, {"version": "2"}]
    registry.get_model_governance_information.return_value = {
        "tags": {"mlflow.user": "alice", "mlflow.runName": "run_1"},
        "params": {"lr": "0.01"},
        "metrics": {"accuracy": "0.95"},
        "run_id": "abc123",
    }
    pool.get_registry_adapter.return_value = registry
    return pool


@pytest.fixture
def mock_platform_config_handler():
    handler = MagicMock()
    handler.get.return_value = "permissive"
    return handler


def tracking_uri_builder(project_name):
    return f"http://{project_name}.svc.cluster.local:5000"


class TestComputeSummary:
    def test_empty_data(self):
        summary = _compute_summary([])
        assert summary.total_projects == 0
        assert summary.total_models == 0
        assert summary.total_versions == 0

    def test_counts_correctly(self):
        data = [
            ProjectData(
                name="proj",
                models=[
                    ModelVersionData(
                        model_name="m1",
                        version="1",
                        risk_level="high",
                        deterministic_compliance="compliant",
                        llm_compliance="not_evaluated",
                    ),
                    ModelVersionData(
                        model_name="m1",
                        version="2",
                        risk_level="high",
                        deterministic_compliance="non_compliant",
                        llm_compliance="compliant",
                    ),
                    ModelVersionData(
                        model_name="m2",
                        version="1",
                        risk_level="minimal",
                        deterministic_compliance="compliant",
                        llm_compliance="compliant",
                    ),
                ],
            )
        ]
        summary = _compute_summary(data)
        assert summary.total_projects == 1
        assert summary.total_models == 2
        assert summary.total_versions == 3
        assert summary.risk_distribution == {"high": 2, "minimal": 1}
        assert summary.deterministic_distribution == {"compliant": 2, "non_compliant": 1}


AI_ACT_CARD_SAMPLE = """\
# Fiche de conformite IA

## 1. Identification du systeme d'IA

| Champ | Valeur |
|---|---|
| **Nom du systeme** | model_x |
| **Version** | 1 |
| **Projet** | test_project |
| **Identifiant de run** | `abc123` |
| **Date de creation** | 2026-03-15 |
| **Equipe / responsable** | alice |

---

## 2. Classification du risque

- [ ] **Risque inacceptable**
- [x] **Risque eleve**
- [ ] **Risque limite**
- [ ] **Risque minimal**

> **Justification** : a completer

## 3. Documentation technique

| Champ | Valeur |
|---|---|
| **Type de modele** | sklearn |
| **Signature - entrees** | [{"name": "feature", "type": "double"}] |
| **Signature - sorties** | [{"name": "prediction", "type": "double"}] |

| Risque | Probabilite | Impact | Mesure de mitigation |
|---|---|---|---|
| *a completer* | *a completer* | *a completer* | *a completer* |
"""


class TestBuildPdf:
    def test_generates_valid_pdf(self):
        data = [
            ProjectData(
                name="test_project",
                models=[
                    ModelVersionData(
                        model_name="model_x",
                        version="1",
                        risk_level="high",
                        deterministic_compliance="compliant",
                        llm_compliance="not_evaluated",
                        author="alice",
                        ai_act_card=AI_ACT_CARD_SAMPLE,
                        model_card="Model card content",
                        params={"lr": "0.01"},
                        metrics={"accuracy": "0.95"},
                        tags={"mlflow.user": "alice"},
                    ),
                ],
            ),
            ProjectData(name="empty_project", models=[]),
            ProjectData(name="error_project", error="Registry unreachable"),
        ]
        summary = _compute_summary(data)
        pdf_path = _build_pdf(data, summary, "permissive")

        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0

        # Verify it's a valid PDF
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"

        os.unlink(pdf_path)

    def test_pdf_with_real_ai_act_template(self):
        """Test with actual AI Act template content including long table rows."""
        from backend.domain.use_cases.ai_act_usecases import _load_template

        template = _load_template()
        # Fill template with realistic data including long JSON signatures
        ai_act_card = template.format_map(
            {
                "model_name": "fraud_detector",
                "version": "3",
                "project_name": "banking",
                "run_id": "abc123def456",
                "run_name": "training_run_42",
                "created_date": "2026-03-15 10:00 UTC",
                "user": "alice@octo.com",
                "risk_level_checkboxes": "- [x] **Risque eleve**\n- [ ] **Risque minimal**",
                "description": "A fraud detection model for banking transactions.",
                "model_type": "sklearn.ensemble.RandomForestClassifier",
                "sig_inputs": '[{"name": "amount", "type": "double"}, {"name": "merchant_category", "type": "string"}]',
                "sig_outputs": '[{"name": "is_fraud", "type": "boolean"}, {"name": "confidence", "type": "double"}]',
                "params_table": "| Parametre | Valeur |\n|---|---|\n| `n_estimators` | `100` |\n| `max_depth` | `10` |",
                "metrics_table": "| Metrique | Valeur | Seuil |\n|---|---|---|\n| `accuracy` | `0.95` | *N/A* |",
                "now_str": "2026-03-15",
            }
        )
        data = [
            ProjectData(
                name="banking",
                models=[
                    ModelVersionData(
                        model_name="fraud_detector",
                        version="3",
                        risk_level="high",
                        deterministic_compliance="compliant",
                        llm_compliance="compliant",
                        author="alice@octo.com",
                        ai_act_card=ai_act_card,
                        act_review="## Review\n\nScore de completude : 8/10\n\nGood compliance.",
                        model_card="Fraud detection model card",
                        params={"n_estimators": "100", "max_depth": "10"},
                        metrics={"accuracy": "0.95", "f1_score": "0.92"},
                        tags={"mlflow.user": "alice@octo.com"},
                    ),
                ],
            ),
        ]
        summary = _compute_summary(data)
        pdf_path = _build_pdf(data, summary, "strict")

        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000  # Should be a substantial PDF
        with open(pdf_path, "rb") as f:
            assert f.read(5) == b"%PDF-"
        os.unlink(pdf_path)

    def test_empty_platform(self):
        data = []
        summary = _compute_summary(data)
        pdf_path = _build_pdf(data, summary, "disabled")

        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0
        os.unlink(pdf_path)


class TestCollectPlatformData:
    @patch("backend.domain.use_cases.compliance_report_usecases.generate_ai_act_card")
    @patch("backend.domain.use_cases.compliance_report_usecases._get_project_models_versions")
    def test_collects_data(
        self, mock_get_versions, mock_gen_card, mock_project_db_handler, mock_model_info_db_handler, mock_registry_pool
    ):
        mock_get_versions.return_value = {"model_1": [{"version": "1"}, {"version": "2"}]}
        mock_gen_card.return_value = "# AI Act Card"

        data = _collect_platform_data(
            mock_project_db_handler, mock_model_info_db_handler, mock_registry_pool, tracking_uri_builder
        )

        assert len(data) == 2
        assert data[0].name == "project_a"
        assert len(data[0].models) == 2
        assert data[0].models[0].model_name == "model_1"
        assert data[0].models[0].risk_level == "high"

    @patch("backend.domain.use_cases.compliance_report_usecases.generate_ai_act_card")
    @patch("backend.domain.use_cases.compliance_report_usecases._get_project_models_versions")
    def test_resilience_on_registry_error(
        self, mock_get_versions, mock_gen_card, mock_project_db_handler, mock_model_info_db_handler, mock_registry_pool
    ):
        mock_registry_pool.get_registry_adapter.side_effect = Exception("Connection refused")

        data = _collect_platform_data(
            mock_project_db_handler, mock_model_info_db_handler, mock_registry_pool, tracking_uri_builder
        )

        assert len(data) == 2
        assert data[0].error is not None
        assert data[1].error is not None


class TestGenerateReport:
    @patch("backend.domain.use_cases.compliance_report_usecases._build_pdf")
    @patch("backend.domain.use_cases.compliance_report_usecases._compute_summary")
    @patch("backend.domain.use_cases.compliance_report_usecases._collect_platform_data")
    def test_end_to_end(
        self,
        mock_collect,
        mock_summary,
        mock_build,
        mock_project_db_handler,
        mock_model_info_db_handler,
        mock_registry_pool,
        mock_platform_config_handler,
    ):
        mock_collect.return_value = [ProjectData(name="p1")]
        mock_summary.return_value = PlatformSummary()
        mock_build.return_value = "/tmp/report.pdf"

        result = generate_platform_compliance_report(
            mock_project_db_handler,
            mock_model_info_db_handler,
            mock_registry_pool,
            mock_platform_config_handler,
            tracking_uri_builder,
        )

        assert result == "/tmp/report.pdf"
        mock_collect.assert_called_once()
        mock_summary.assert_called_once()
        mock_build.assert_called_once()
