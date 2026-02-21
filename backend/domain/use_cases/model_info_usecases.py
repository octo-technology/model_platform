# Philippe Stepniewski
from backend.domain.entities.model_info import ModelInfo
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.model_registry import ModelRegistry
from backend.infrastructure.model_info_sqlite_db_handler import ModelInfoAlreadyExistError


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
            try:
                model_info_db_handler.add_model_info(
                    ModelInfo(
                        model_name=model["name"],
                        model_version=version_dict["version"],
                        project_name=project_name,
                        model_card=model_card,
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
