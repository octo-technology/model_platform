# Philippe Stepniewski
import os
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from fpdf import FPDF
from loguru import logger

from backend.domain.entities.model_info import ModelInfo
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.model_registry import ModelRegistry
from backend.domain.ports.platform_config_handler import PlatformConfigHandler
from backend.domain.ports.project_db_handler import ProjectDbHandler
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.use_cases.ai_act_usecases import generate_ai_act_card
from backend.domain.use_cases.compliance_usecases import DEPLOYMENT_GATE_POLICY_KEY, GATE_POLICY_PERMISSIVE


@dataclass
class ModelVersionData:
    model_name: str
    version: str
    risk_level: str | None = None
    deterministic_compliance: str | None = None
    llm_compliance: str | None = None
    author: str | None = None
    ai_act_card: str | None = None
    act_review: str | None = None
    model_card: str | None = None
    params: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    tags: dict = field(default_factory=dict)


@dataclass
class ProjectData:
    name: str
    models: list[ModelVersionData] = field(default_factory=list)
    error: str | None = None


@dataclass
class PlatformSummary:
    total_projects: int = 0
    total_models: int = 0
    total_versions: int = 0
    risk_distribution: dict[str, int] = field(default_factory=dict)
    deterministic_distribution: dict[str, int] = field(default_factory=dict)
    llm_distribution: dict[str, int] = field(default_factory=dict)


def _get_project_models_versions(registry: ModelRegistry) -> dict:
    project_models = registry.list_all_models()
    model_versions = {}
    for model in project_models:
        model_name = model["name"]
        model_versions[model_name] = registry.list_model_versions(model_name)
    return model_versions


def _collect_platform_data(
    project_db_handler: ProjectDbHandler,
    model_info_db_handler: ModelInfoDbHandler,
    registry_pool: RegistryHandler,
    tracking_uri_builder: Callable[[str], str],
) -> list[ProjectData]:
    projects = project_db_handler.list_projects()
    platform_data = []

    for project in projects:
        project_name = project.name
        project_data = ProjectData(name=project_name)

        try:
            registry: ModelRegistry = registry_pool.get_registry_adapter(
                project_name, tracking_uri_builder(project_name)
            )
            model_versions = _get_project_models_versions(registry)
            model_infos = model_info_db_handler.list_model_infos_for_project(project_name)
            model_info_map: dict[tuple[str, str], ModelInfo] = {
                (mi.model_name, mi.model_version): mi for mi in model_infos
            }

            for model_name, versions in model_versions.items():
                for version_entry in versions:
                    version = version_entry["version"]
                    mi = model_info_map.get((model_name, version))

                    governance = {}
                    try:
                        governance = registry.get_model_governance_information(model_name, version)
                    except Exception:
                        pass

                    tags = governance.get("tags", {})
                    author = tags.get("mlflow.user")

                    ai_act_md = None
                    try:
                        ai_act_md = generate_ai_act_card(
                            registry, model_info_db_handler, project_name, model_name, version
                        )
                    except Exception:
                        logger.warning(f"Could not generate AI Act card for {model_name}:{version} in {project_name}")

                    mvd = ModelVersionData(
                        model_name=model_name,
                        version=version,
                        risk_level=mi.risk_level if mi else None,
                        deterministic_compliance=mi.deterministic_compliance if mi else "not_evaluated",
                        llm_compliance=mi.llm_compliance if mi else "not_evaluated",
                        author=author,
                        ai_act_card=ai_act_md,
                        act_review=mi.act_review if mi else None,
                        model_card=mi.model_card if mi else None,
                        params=governance.get("params", {}),
                        metrics=governance.get("metrics", {}),
                        tags=tags,
                    )
                    project_data.models.append(mvd)

        except Exception as e:
            logger.warning(f"Could not access registry for project {project_name}: {e}")
            project_data.error = str(e)

        platform_data.append(project_data)

    return platform_data


def _compute_summary(platform_data: list[ProjectData]) -> PlatformSummary:
    risk_counter: Counter = Counter()
    det_counter: Counter = Counter()
    llm_counter: Counter = Counter()
    total_models = set()
    total_versions = 0

    for project in platform_data:
        for mv in project.models:
            total_models.add((project.name, mv.model_name))
            total_versions += 1
            risk_counter[mv.risk_level or "non renseigne"] += 1
            det_counter[mv.deterministic_compliance or "not_evaluated"] += 1
            llm_counter[mv.llm_compliance or "not_evaluated"] += 1

    return PlatformSummary(
        total_projects=len(platform_data),
        total_models=len(total_models),
        total_versions=total_versions,
        risk_distribution=dict(risk_counter),
        deterministic_distribution=dict(det_counter),
        llm_distribution=dict(llm_counter),
    )


class ComplianceReportPDF(FPDF):
    NAVY = (14, 35, 86)
    TURQUOISE = (0, 163, 190)
    WHITE = (255, 255, 255)

    def __init__(self, generation_date: str, gate_policy: str):
        super().__init__()
        self.generation_date = generation_date
        self.gate_policy = gate_policy
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.NAVY)
        self.cell(0, 8, "Model Platform", align="L")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 8, self.generation_date, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.TURQUOISE)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def cover_page(self, summary: PlatformSummary):
        self.add_page()
        self.ln(50)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*self.NAVY)
        self.multi_cell(0, 14, _safe("Rapport de Conformite\nIA Act"), align="C")
        self.ln(8)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*self.TURQUOISE)
        self.cell(0, 10, "Plateforme Model Platform", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(12)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, f"Date de generation : {self.generation_date}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 8, f"Politique de gate : {self.gate_policy}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)
        self.set_font("Helvetica", "", 11)
        self.cell(
            0,
            8,
            f"{summary.total_projects} projets  |  {summary.total_models} modeles  |  "
            f"{summary.total_versions} versions",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    def _section_title(self, title: str):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*self.NAVY)
        self.cell(0, 12, _safe(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.TURQUOISE)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def _sub_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*self.NAVY)
        self.cell(0, 10, _safe(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def _distribution_table(self, title: str, distribution: dict[str, int]):
        self._sub_title(title)
        col_w = 70
        val_w = 30
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(*self.NAVY)
        self.set_text_color(*self.WHITE)
        self.cell(col_w, 8, "Statut", border=1, fill=True)
        self.cell(val_w, 8, "Nombre", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        for status, count in sorted(distribution.items(), key=lambda x: -x[1]):
            self.cell(col_w, 7, _safe(status), border=1)
            self.cell(val_w, 7, str(count), border=1, new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def executive_summary(self, summary: PlatformSummary):
        self.add_page()
        self._section_title("Resume executif")

        self.set_font("Helvetica", "", 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(
            0,
            7,
            _safe(
                f"Ce rapport couvre l'ensemble des modeles de la plateforme Model Platform. "
                f"Il recense {summary.total_projects} projet(s), {summary.total_models} modele(s) "
                f"et {summary.total_versions} version(s) de modeles."
            ),
        )
        self.ln(6)

        self._distribution_table("Distribution des niveaux de risque", summary.risk_distribution)
        self._distribution_table("Conformite deterministe", summary.deterministic_distribution)
        self._distribution_table("Conformite LLM", summary.llm_distribution)

    def project_section(self, project_data: ProjectData):
        self.add_page()
        self._section_title(f"Projet : {project_data.name}")

        if project_data.error:
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(180, 0, 0)
            self.multi_cell(0, 7, _safe(f"Donnees indisponibles : {project_data.error}"))
            return

        if not project_data.models:
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 7, "Aucun modele enregistre dans ce projet.", new_x="LMARGIN", new_y="NEXT")
            return

        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, f"Nombre de modeles-versions : {len(project_data.models)}", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        # Table header
        col_widths = [35, 15, 30, 35, 35, 30]
        headers = ["Modele", "Ver.", "Risque", "Compliance Det.", "Compliance LLM", "Auteur"]
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*self.NAVY)
        self.set_text_color(*self.WHITE)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True)
        self.ln()

        # Table rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(0, 0, 0)
        for mv in project_data.models:
            row = [
                _truncate(mv.model_name, 20),
                mv.version,
                mv.risk_level or "N/A",
                mv.deterministic_compliance or "N/A",
                mv.llm_compliance or "N/A",
                _truncate(mv.author or "N/A", 16),
            ]
            for i, val in enumerate(row):
                self.cell(col_widths[i], 6, _safe(val), border=1)
            self.ln()

    def annex_ai_act_card(self, model_name: str, version: str, ai_act_markdown: str):
        self.add_page()
        self._section_title(f"Annexe A : Fiche IA Act — {model_name} v{version}")
        self._render_markdown(ai_act_markdown)

    def annex_act_review(self, model_name: str, version: str, review_markdown: str):
        self.add_page()
        self._section_title(f"Annexe B : Review LLM — {model_name} v{version}")
        self._render_markdown(review_markdown)

    def annex_model_card(self, model_name: str, version: str, model_card: str):
        self.add_page()
        self._section_title(f"Annexe C : Model Card — {model_name} v{version}")
        self._render_markdown(model_card)

    def annex_metadata(self, model_name: str, version: str, mv: ModelVersionData):
        self.add_page()
        self._section_title(f"Annexe D : Metadonnees — {model_name} v{version}")

        if mv.params:
            self._sub_title("Hyperparametres")
            self._key_value_table(mv.params)

        if mv.metrics:
            self._sub_title("Metriques")
            self._key_value_table(mv.metrics)

        if mv.tags:
            self._sub_title("Tags MLflow")
            filtered_tags = {k: v for k, v in mv.tags.items() if not k.startswith("mlflow.log-model.history")}
            self._key_value_table(filtered_tags)

    def _key_value_table(self, data: dict):
        col_k = 60
        col_v = 110
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*self.NAVY)
        self.set_text_color(*self.WHITE)
        self.cell(col_k, 7, "Cle", border=1, fill=True)
        self.cell(col_v, 7, "Valeur", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(0, 0, 0)
        for k, v in data.items():
            self.cell(col_k, 6, _safe(_truncate(str(k), 35)), border=1)
            self.cell(col_v, 6, _safe(_truncate(str(v), 65)), border=1, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def _safe_multi_cell(self, w, h, text):
        """multi_cell with x-position reset and error handling."""
        self.set_x(self.l_margin)
        try:
            self.multi_cell(w, h, text)
        except Exception:
            # Fallback: truncate aggressively and retry
            max_chars = int((self.w - self.l_margin - self.r_margin) / 2)
            self.multi_cell(w, h, _truncate(text, max_chars))

    def _render_markdown_table(self, table_lines: list[str]):
        """Parse markdown table lines and render as a native fpdf2 table."""
        rows = []
        for line in table_lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)

        if not rows:
            return

        num_cols = len(rows[0])
        available_w = self.w - self.l_margin - self.r_margin
        col_w = available_w / max(num_cols, 1)
        # At font size 8, ~2.2mm per char. Leave margin for border.
        max_chars = max(int(col_w / 2.2) - 1, 5)

        self.set_x(self.l_margin)

        # Header row
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*self.NAVY)
        self.set_text_color(*self.WHITE)
        for i, cell in enumerate(rows[0]):
            last = i == num_cols - 1
            self.cell(
                col_w,
                6,
                _safe(_truncate(cell.strip("*"), max_chars)),
                border=1,
                fill=True,
                new_x="LMARGIN" if last else "RIGHT",
                new_y="NEXT" if last else "TOP",
            )

        # Data rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(0, 0, 0)
        for row in rows[1:]:
            for i, cell in enumerate(row[:num_cols]):
                last = i == num_cols - 1
                self.cell(
                    col_w,
                    5,
                    _safe(_truncate(cell, max_chars)),
                    border=1,
                    new_x="LMARGIN" if last else "RIGHT",
                    new_y="NEXT" if last else "TOP",
                )
        self.ln(4)

    def _render_markdown(self, text: str):
        self.set_text_color(0, 0, 0)
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()

            # Collect markdown table blocks
            if stripped.startswith("|") and "|" in stripped[1:]:
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    row = lines[i].strip()
                    # Skip separator rows like |---|---|
                    if not all(c in "|-: " for c in row):
                        table_lines.append(row)
                    i += 1
                if table_lines:
                    self._render_markdown_table(table_lines)
                continue

            if stripped.startswith("### "):
                self.set_font("Helvetica", "B", 11)
                self._safe_multi_cell(0, 6, _safe(stripped[4:]))
                self.ln(2)
            elif stripped.startswith("## "):
                self.set_font("Helvetica", "B", 13)
                self.set_text_color(*self.NAVY)
                self._safe_multi_cell(0, 7, _safe(stripped[3:]))
                self.set_text_color(0, 0, 0)
                self.ln(2)
            elif stripped.startswith("# "):
                self.set_font("Helvetica", "B", 15)
                self.set_text_color(*self.NAVY)
                self._safe_multi_cell(0, 8, _safe(stripped[2:]))
                self.set_text_color(0, 0, 0)
                self.ln(3)
            elif stripped.startswith("- ["):
                self.set_font("Helvetica", "", 10)
                self._safe_multi_cell(0, 6, _safe("  " + stripped))
            elif stripped.startswith("- ") or stripped.startswith("* "):
                self.set_font("Helvetica", "", 10)
                self._safe_multi_cell(0, 6, _safe("  " + stripped))
            elif stripped.startswith("> "):
                self.set_font("Helvetica", "I", 9)
                self._safe_multi_cell(0, 6, _safe(stripped[2:]))
            elif stripped == "---":
                self.set_draw_color(*self.TURQUOISE)
                self.set_line_width(0.3)
                y = self.get_y()
                self.line(self.l_margin, y, self.w - self.r_margin, y)
                self.ln(4)
            elif stripped.startswith("**") and stripped.endswith("**"):
                self.set_font("Helvetica", "B", 10)
                self._safe_multi_cell(0, 6, _safe(stripped.strip("*")))
            elif stripped:
                self.set_font("Helvetica", "", 10)
                self._safe_multi_cell(0, 6, _safe(stripped))
            else:
                self.ln(3)

            i += 1


def _safe(text: str) -> str:
    """Replace characters unsupported by Helvetica (latin-1) with ASCII equivalents."""
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00e9": "e",
        "\u00e8": "e",
        "\u00ea": "e",
        "\u00eb": "e",
        "\u00e0": "a",
        "\u00e2": "a",
        "\u00f4": "o",
        "\u00fb": "u",
        "\u00f9": "u",
        "\u00ee": "i",
        "\u00ef": "i",
        "\u00e7": "c",
        "\u00c9": "E",
        "\u00c8": "E",
        "\u00ca": "E",
        "\u00c0": "A",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", "replace").decode("latin-1")


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _build_pdf(platform_data: list[ProjectData], summary: PlatformSummary, gate_policy: str) -> str:
    generation_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf = ComplianceReportPDF(generation_date=generation_date, gate_policy=gate_policy)
    pdf.alias_nb_pages()

    # Cover page
    pdf.cover_page(summary)

    # Executive summary
    pdf.executive_summary(summary)

    # Per-project sections
    for project_data in platform_data:
        pdf.project_section(project_data)

    # Annexes
    for project_data in platform_data:
        for mv in project_data.models:
            if mv.ai_act_card:
                pdf.annex_ai_act_card(mv.model_name, mv.version, mv.ai_act_card)
            if mv.act_review:
                pdf.annex_act_review(mv.model_name, mv.version, mv.act_review)
            if mv.model_card:
                pdf.annex_model_card(mv.model_name, mv.version, mv.model_card)
            if mv.params or mv.metrics or mv.tags:
                pdf.annex_metadata(mv.model_name, mv.version, mv)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(tempfile.gettempdir(), f"platform_compliance_report_{timestamp}.pdf")
    pdf.output(pdf_path)
    return pdf_path


def get_platform_dashboard_data(
    project_db_handler: ProjectDbHandler,
    model_info_db_handler: ModelInfoDbHandler,
    registry_pool: RegistryHandler,
    platform_config_handler: PlatformConfigHandler,
    tracking_uri_builder: Callable[[str], str],
) -> dict:
    """Return lightweight platform-wide compliance data for the dashboard (no AI Act card generation)."""
    gate_policy = platform_config_handler.get(DEPLOYMENT_GATE_POLICY_KEY) or GATE_POLICY_PERMISSIVE
    projects = project_db_handler.list_projects()
    project_summaries = []

    risk_counter: Counter = Counter()
    det_counter: Counter = Counter()
    llm_counter: Counter = Counter()
    total_models = set()
    total_versions = 0

    for project in projects:
        project_name = project.name
        project_risk: Counter = Counter()
        project_det: Counter = Counter()
        project_llm: Counter = Counter()
        project_version_count = 0
        project_model_names = set()
        error = None

        try:
            registry: ModelRegistry = registry_pool.get_registry_adapter(
                project_name, tracking_uri_builder(project_name)
            )
            model_versions_map = _get_project_models_versions(registry)
            model_infos = model_info_db_handler.list_model_infos_for_project(project_name)
            model_info_map: dict[tuple[str, str], ModelInfo] = {
                (mi.model_name, mi.model_version): mi for mi in model_infos
            }

            for model_name, versions in model_versions_map.items():
                for version_entry in versions:
                    version = version_entry["version"]
                    mi = model_info_map.get((model_name, version))
                    project_version_count += 1
                    total_versions += 1
                    project_model_names.add(model_name)
                    total_models.add((project_name, model_name))

                    rl = mi.risk_level if mi else None
                    dc = mi.deterministic_compliance if mi else "not_evaluated"
                    lc = mi.llm_compliance if mi else "not_evaluated"

                    project_risk[rl or "non renseigne"] += 1
                    risk_counter[rl or "non renseigne"] += 1
                    project_det[dc or "not_evaluated"] += 1
                    det_counter[dc or "not_evaluated"] += 1
                    project_llm[lc or "not_evaluated"] += 1
                    llm_counter[lc or "not_evaluated"] += 1

        except Exception as e:
            logger.warning(f"Could not access registry for project {project_name}: {e}")
            error = str(e)

        project_summaries.append(
            {
                "name": project_name,
                "total_models": len(project_model_names),
                "total_versions": project_version_count,
                "risk_distribution": dict(project_risk),
                "deterministic_distribution": dict(project_det),
                "llm_distribution": dict(project_llm),
                "error": error,
            }
        )

    return {
        "gate_policy": gate_policy,
        "summary": {
            "total_projects": len(projects),
            "total_models": len(total_models),
            "total_versions": total_versions,
            "risk_distribution": dict(risk_counter),
            "deterministic_distribution": dict(det_counter),
            "llm_distribution": dict(llm_counter),
        },
        "projects": project_summaries,
    }


def generate_platform_compliance_report(
    project_db_handler: ProjectDbHandler,
    model_info_db_handler: ModelInfoDbHandler,
    registry_pool: RegistryHandler,
    platform_config_handler: PlatformConfigHandler,
    tracking_uri_builder: Callable[[str], str],
) -> str:
    """Generate a full platform compliance PDF report. Returns the path to the PDF file."""
    gate_policy = platform_config_handler.get(DEPLOYMENT_GATE_POLICY_KEY) or GATE_POLICY_PERMISSIVE
    platform_data = _collect_platform_data(
        project_db_handler, model_info_db_handler, registry_pool, tracking_uri_builder
    )
    summary = _compute_summary(platform_data)
    return _build_pdf(platform_data, summary, gate_policy)
