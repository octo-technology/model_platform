# Philippe Stepniewski
from loguru import logger

from backend.domain.entities.model_info import ModelInfo
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.model_registry import ModelRegistry
from backend.infrastructure.model_info_sqlite_db_handler import ModelInfoAlreadyExistError

RISK_LEVEL_MAPPING = {
    "inacceptable": "unacceptable",
    "élevé": "high",
    "eleve": "high",
    "limité": "limited",
    "limite": "limited",
    "minimal": "minimal",
    "unacceptable": "unacceptable",
    "high": "high",
    "limited": "limited",
}


def _extract_risk_level_from_tags(tags: dict) -> str | None:
    raw = tags.get("ai_act_risk_level")
    if not raw:
        return None
    return RISK_LEVEL_MAPPING.get(raw.lower().strip(), raw.lower().strip())


def search_model_infos(
    query: str,
    model_info_db_handler: ModelInfoDbHandler,
    project_name: str | None = None,
) -> list[ModelInfo]:
    return model_info_db_handler.search_model_infos(query=query, project_name=project_name)


def sync_model_infos_for_project(
    project_name: str,
    registry: ModelRegistry,
    model_info_db_handler: ModelInfoDbHandler,
) -> None:
    models = registry.list_all_models()
    for model in models:
        versions = registry.list_model_versions(model["name"])
        for version_dict in versions:
            model_card = registry.get_model_card(model["name"], version_dict["version"])

            risk_level = None
            try:
                governance = registry.get_model_governance_information(model["name"], version_dict["version"])
                risk_level = _extract_risk_level_from_tags(governance.get("tags", {}))
            except Exception:
                logger.warning(f"Could not get governance info for {model['name']}:{version_dict['version']}")

            try:
                model_info_db_handler.add_model_info(
                    ModelInfo(
                        model_name=model["name"],
                        model_version=version_dict["version"],
                        project_name=project_name,
                        model_card=model_card,
                        risk_level=risk_level,
                    )
                )
            except ModelInfoAlreadyExistError:
                if model_card is not None:
                    model_info_db_handler.update_model_card(
                        model_name=model["name"],
                        model_version=version_dict["version"],
                        project_name=project_name,
                        model_card=model_card,
                    )
                if risk_level is not None:
                    model_info_db_handler.update_risk_level(
                        model_name=model["name"],
                        model_version=version_dict["version"],
                        project_name=project_name,
                        risk_level=risk_level,
                    )
