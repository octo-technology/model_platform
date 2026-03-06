import json
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


def _format_created_date(tags: dict) -> str:
    history_raw = tags.get("mlflow.log-model.history")
    if history_raw:
        try:
            history = json.loads(history_raw)
            if isinstance(history, list) and history and history[0].get("utc_time_created"):
                return history[0]["utc_time_created"]
        except (json.JSONDecodeError, KeyError):
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _extract_model_type(tags: dict) -> str:
    history_raw = tags.get("mlflow.log-model.history")
    if history_raw:
        try:
            history = json.loads(history_raw)
            if isinstance(history, list) and history:
                flavours = history[0].get("flavors", {})
                non_pyfunc = [f for f in flavours if f != "python_function"]
                if non_pyfunc:
                    return ", ".join(non_pyfunc)
        except (json.JSONDecodeError, KeyError):
            pass
    return "*à compléter*"


def _extract_signature(tags: dict) -> tuple[str, str]:
    history_raw = tags.get("mlflow.log-model.history")
    if history_raw:
        try:
            history = json.loads(history_raw)
            if isinstance(history, list) and history:
                sig = history[0].get("signature", {})
                inputs = sig.get("inputs", "*à compléter*")
                outputs = sig.get("outputs", "*à compléter*")
                return str(inputs), str(outputs)
        except (json.JSONDecodeError, KeyError):
            pass
    return "*à compléter*", "*à compléter*"


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
    run_id: str = governance.get("run_id", "N/A")

    model_info: ModelInfo | None = model_info_db_handler.get_model_info(model_name, version, project_name)
    risk_level = model_info.risk_level if model_info else None
    model_card_text = model_info.model_card if model_info else None

    context = {
        "model_name": model_name,
        "version": version,
        "project_name": project_name,
        "run_id": run_id,
        "run_name": tags.get("mlflow.runName", "N/A"),
        "created_date": _format_created_date(tags),
        "user": tags.get("mlflow.user", "*à compléter*"),
        "risk_level_checkboxes": _risk_level_checkboxes(risk_level),
        "description": model_card_text or tags.get("mlflow.note.content") or "*à compléter*",
        "model_type": _extract_model_type(tags),
        "sig_inputs": _extract_signature(tags)[0],
        "sig_outputs": _extract_signature(tags)[1],
        "params_table": _params_table(params),
        "metrics_table": _metrics_table(metrics),
        "now_str": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    return _load_template().format_map(context)
