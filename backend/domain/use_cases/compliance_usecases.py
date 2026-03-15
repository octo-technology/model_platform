# Philippe Stepniewski
import re

from backend.domain.entities.model_info import ModelInfo
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.model_registry import ModelRegistry
from backend.domain.ports.platform_config_handler import PlatformConfigHandler

COMPLIANCE_NOT_EVALUATED = "not_evaluated"
COMPLIANCE_NON_COMPLIANT = "non_compliant"
COMPLIANCE_PARTIALLY_COMPLIANT = "partially_compliant"
COMPLIANCE_COMPLIANT = "compliant"

GATE_POLICY_STRICT = "strict"
GATE_POLICY_PERMISSIVE = "permissive"
GATE_POLICY_DISABLED = "disabled"

DEPLOYMENT_GATE_POLICY_KEY = "DEPLOYMENT_GATE_POLICY"


def evaluate_deterministic_compliance(model_info: ModelInfo, governance: dict) -> str:
    """Evaluate deterministic compliance based on model metadata.

    Returns one of: compliant, partially_compliant, non_compliant.
    """
    tags: dict = governance.get("tags", {})
    params: dict = governance.get("params", {})
    metrics: dict = governance.get("metrics", {})

    # Immediate rejection for unacceptable risk
    if model_info.risk_level == "unacceptable":
        return COMPLIANCE_NON_COMPLIANT

    # Mandatory criteria
    has_risk_level = bool(model_info.risk_level)
    has_model_card = bool(model_info.model_card) or bool(tags.get("mlflow.note.content"))
    has_metrics = len(metrics) > 0
    has_author = bool(tags.get("mlflow.user"))

    mandatory_ok = all([has_risk_level, has_model_card, has_metrics, has_author])

    if not mandatory_ok:
        return COMPLIANCE_NON_COMPLIANT

    # Recommended criteria
    has_params = len(params) > 0
    has_signature = _has_model_signature(tags)
    recommended_count = sum([has_params, has_signature])

    if recommended_count >= 1:
        return COMPLIANCE_COMPLIANT

    return COMPLIANCE_PARTIALLY_COMPLIANT


def _has_model_signature(tags: dict) -> bool:
    import json

    history_raw = tags.get("mlflow.log-model.history")
    if not history_raw:
        return False
    try:
        history = json.loads(history_raw)
        if isinstance(history, list) and history:
            sig = history[0].get("signature")
            return sig is not None and sig != {}
    except (json.JSONDecodeError, KeyError):
        pass
    return False


def extract_llm_compliance_from_review(act_review: str | None) -> str:
    """Extract compliance status from the LLM act_review markdown.

    Looks for a pattern like "Score de complétude" followed by X/10.
    """
    if not act_review:
        return COMPLIANCE_NOT_EVALUATED

    pattern = r"[Ss]core\s+de\s+compl[eé]tude[^0-9]*(\d{1,2})\s*/\s*10"
    match = re.search(pattern, act_review)
    if not match:
        return COMPLIANCE_NOT_EVALUATED

    score = int(match.group(1))
    if score >= 7:
        return COMPLIANCE_COMPLIANT
    if score >= 4:
        return COMPLIANCE_PARTIALLY_COMPLIANT
    return COMPLIANCE_NON_COMPLIANT


def evaluate_project_compliance(
    project_name: str,
    registry: ModelRegistry,
    model_info_db_handler: ModelInfoDbHandler,
) -> list[dict]:
    """Recalculate deterministic compliance for all models in a project."""
    model_infos = model_info_db_handler.list_model_infos_for_project(project_name)
    results = []
    for model_info in model_infos:
        try:
            governance = registry.get_model_governance_information(model_info.model_name, model_info.model_version)
        except Exception:
            governance = {"tags": {}, "params": {}, "metrics": {}}

        status = evaluate_deterministic_compliance(model_info, governance)
        model_info_db_handler.update_compliance_statuses(
            model_name=model_info.model_name,
            model_version=model_info.model_version,
            project_name=project_name,
            deterministic_compliance=status,
        )
        results.append(
            {
                "model_name": model_info.model_name,
                "model_version": model_info.model_version,
                "deterministic_compliance": status,
            }
        )
    return results


def check_deployment_gate(
    model_info: ModelInfo,
    platform_config_handler: PlatformConfigHandler,
) -> tuple[bool, str]:
    """Check if deployment is allowed based on compliance statuses and gate policy.

    Returns (allowed, reason).
    """
    policy = platform_config_handler.get(DEPLOYMENT_GATE_POLICY_KEY) or GATE_POLICY_PERMISSIVE

    if policy == GATE_POLICY_DISABLED:
        return True, ""

    det = model_info.deterministic_compliance or COMPLIANCE_NOT_EVALUATED
    llm = model_info.llm_compliance or COMPLIANCE_NOT_EVALUATED

    passing_statuses = {COMPLIANCE_COMPLIANT, COMPLIANCE_PARTIALLY_COMPLIANT}
    det_ok = det in passing_statuses
    llm_ok = llm in passing_statuses

    if policy == GATE_POLICY_STRICT:
        if det_ok and llm_ok:
            return True, ""
        reasons = []
        if not det_ok:
            reasons.append(f"deterministic compliance: {det}")
        if not llm_ok:
            reasons.append(f"LLM compliance: {llm}")
        return False, f"Deployment blocked (strict policy). {', '.join(reasons)}."

    # permissive: at least one must pass
    if det_ok or llm_ok:
        return True, ""
    return (
        False,
        f"Deployment blocked (permissive policy). deterministic: {det}, LLM: {llm}. "
        f"At least one must be compliant or partially compliant.",
    )
