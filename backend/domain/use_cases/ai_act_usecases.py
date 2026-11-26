from datetime import datetime, timezone
from pathlib import Path

from backend.domain.entities.model_info import ModelInfo
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.model_registry import ModelRegistry

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "ai_act_card.md"


def _load_template() -> str:
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def _risk_level_checkboxes(risk_level: str | None) -> str:
    levels = {
        "unacceptable": "Risque inacceptable — système interdit (Art. 5)",
        "high": "Risque élevé — conformité obligatoire (Art. 6 + Annexe III)",
        "limited": "Risque limité — obligations de transparence (Art. 50)",
        "minimal": "Risque minimal — aucune obligation spécifique",
    }
    lines = []
    for key, label in levels.items():
        checked = "x" if key == risk_level else " "
        lines.append(f"- [{checked}] **{label}**")
    return "\n".join(lines)


def _params_table(params: dict) -> str:
    if not params:
        return "*Aucun hyperparamètre enregistré.*"
    rows = "\n".join(f"| `{k}` | `{v}` |" for k, v in params.items())
    return f"| Paramètre | Valeur |\n|---|---|\n{rows}"


def _metrics_table(metrics: dict) -> str:
    if not metrics:
        return "*Aucune métrique enregistrée.*"
    rows = "\n".join(f"| `{k}` | `{v}` | *N/A* |" for k, v in metrics.items())
    return f"| Métrique | Valeur | Seuil d'acceptation |\n|---|---|---|\n{rows}"


def _format_created_date(creation_timestamp: int | None) -> str:
    """Format LoggedModel.creation_timestamp (epoch ms) as UTC string."""
    if creation_timestamp:
        try:
            return datetime.fromtimestamp(creation_timestamp / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except (ValueError, OSError):
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _format_model_type(flavors: list[str] | None) -> str:
    """Build a comma-separated list of non-pyfunc flavors."""
    if not flavors:
        return "*à compléter*"
    non_pyfunc = [f for f in flavors if f != "python_function"]
    if not non_pyfunc:
        return "*à compléter*"
    return ", ".join(non_pyfunc)


def _format_signature(signature: dict | None) -> tuple[str, str]:
    """Extract inputs/outputs from a LoggedModel signature dict."""
    if not signature:
        return "*à compléter*", "*à compléter*"
    inputs = signature.get("inputs", "*à compléter*")
    outputs = signature.get("outputs", "*à compléter*")
    return str(inputs), str(outputs)


def generate_ai_act_card(
    registry: ModelRegistry,
    model_info_db_handler: ModelInfoDbHandler,
    project_name: str,
    model_name: str,
    version: str,
) -> str:
    """Generate a Markdown AI Act compliance card for a model version."""
    governance = registry.get_model_governance_information(model_name, version)
    tags: dict = governance.get("tags", {})
    params: dict = governance.get("params", {})
    metrics: dict = governance.get("metrics", {})
    run_id: str = governance.get("run_id") or "N/A"
    flavors: list[str] = governance.get("flavors", []) or []
    signature: dict | None = governance.get("signature")
    creation_timestamp: int | None = governance.get("creation_timestamp")

    model_info: ModelInfo | None = model_info_db_handler.get_model_info(model_name, version, project_name)
    risk_level = model_info.risk_level if model_info else None
    model_card_text = model_info.model_card if model_info else None

    sig_inputs, sig_outputs = _format_signature(signature)

    context = {
        "model_name": model_name,
        "version": version,
        "project_name": project_name,
        "run_id": run_id,
        "run_name": tags.get("mlflow.runName", "N/A"),
        "created_date": _format_created_date(creation_timestamp),
        "user": tags.get("mlflow.user", "*à compléter*"),
        "risk_level_checkboxes": _risk_level_checkboxes(risk_level),
        "description": model_card_text or tags.get("mlflow.note.content") or "*à compléter*",
        "model_type": _format_model_type(flavors),
        "sig_inputs": sig_inputs,
        "sig_outputs": sig_outputs,
        "params_table": _params_table(params),
        "metrics_table": _metrics_table(metrics),
        "now_str": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    return _load_template().format_map(context)
