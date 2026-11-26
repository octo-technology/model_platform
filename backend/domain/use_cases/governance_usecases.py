import json
import os
import shutil

from backend import PROJECT_DIR
from backend.domain.ports.agent_registry import AgentRegistry
from backend.domain.use_cases.files_management import (
    create_tmp_artefacts_folder,
    recreate_directory,
    remove_directory,
)
from backend.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter
from backend.infrastructure.mlflow_client import MLflowClientManager
from backend.infrastructure.mlflow_model_registry_adapter import MLFlowModelRegistryAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()


def _extract_model_artifacts(
    registry: MLFlowModelRegistryAdapter, project_name: str, model_name: str, version: str, path: str
):
    """
    Extract model artifacts from the MLFlow Model Registry
    """
    destination_path = create_tmp_artefacts_folder(model_name, project_name, version, path)
    model_artifacts = registry.download_model_artifacts(model_name, version, destination_path)
    return model_artifacts


def _filter_events_for_model(project_events: list, model_name: str, version: str):
    model_events = []
    for event in project_events or []:
        raw_entity = event.get("entity")
        if not raw_entity:
            continue
        try:
            event_entity = json.loads(raw_entity.replace("'", '"'))
        except (json.JSONDecodeError, AttributeError):
            continue
        if (
            "model_name" in event_entity
            and event_entity["model_name"] == model_name
            and event_entity["version"] == version
        ):
            model_events.append(
                {
                    "action": event.get("action"),
                    "timestamp": event.get("timestamp"),
                    "user": event.get("user"),
                    **event_entity,
                }
            )
    return model_events


def _create_folder_for_governance_artifacts(project_name: str):
    """
    Create a folder for storing governance artifacts
    """
    path_dest = os.path.join(PROJECT_DIR, "tmp", project_name + "_governance_artifacts")
    recreate_directory(path_dest)
    return path_dest


def _get_events_for_model(project_name: str, model_name: str, version: str):
    """
    Get events for a specific model
    """
    project_events: list = EVENT_LOGGER.list_events(project_name)
    model_events = _filter_events_for_model(project_events, model_name, version)
    return model_events


def _get_project_models_versions(registry: MLFlowModelRegistryAdapter):
    project_models = registry.list_all_models()
    model_versions = {}
    for model in project_models:
        model_name = model["name"]
        model_versions[model_name] = registry.list_model_versions(model_name)
    return model_versions


def _extract_agent_artifacts(
    agent_registry: AgentRegistry, project_name: str, agent_name: str, version: str, path: str
):
    """
    Extract agent artifacts from the MLFlow Model Registry
    """
    destination_path = create_tmp_artefacts_folder(agent_name, project_name, version, path)
    agent_artifacts = agent_registry.download_agent_artifacts(agent_name, version, destination_path)
    return agent_artifacts


def _get_project_agents_versions(agent_registry: AgentRegistry):
    project_agents = agent_registry.list_all_agents()
    agent_versions = {}
    for agent in project_agents:
        agent_name = agent["name"]
        agent_versions[agent_name] = agent_registry.list_agent_versions(agent_name)
    return agent_versions


def extract_agent_governance_information(
    agent_registry: AgentRegistry,
    project_name: str,
    agent_name: str,
    version: str,
    creation_timestamp: int | None = None,
):
    """
    Extract agent governance information from the MLFlow Model Registry
    """
    information = agent_registry.get_agent_governance_information(agent_name, version)
    information["creation_timestamp"] = creation_timestamp
    return {"agent_information": information, "events": _get_events_for_model(project_name, agent_name, version)}


def extract_model_governance_information(
    registry: MLFlowModelRegistryAdapter, project_name: str, model_name: str, version: str
):
    """
    Extract model governance information from the MLFlow Model Registry
    """
    information = registry.get_model_governance_information(model_name, version)
    return {"model_information": information, "events": _get_events_for_model(project_name, model_name, version)}


def download_project_models_governance_information(
    project_name: str, registry: MLFlowModelRegistryAdapter, agent_registry: AgentRegistry | None = None
):
    """
    Extract model (and agent, if an agent_registry is given) governance information
    for everything in a project
    """
    project_information = []
    versions = _get_project_models_versions(registry)
    artifacts_path_tmp = _create_folder_for_governance_artifacts(project_name)
    for model_name in versions.keys():
        for version in versions[model_name]:
            version_name = version["version"]
            model_information = extract_model_governance_information(registry, project_name, model_name, version_name)
            _extract_model_artifacts(registry, project_name, model_name, version_name, artifacts_path_tmp)
            project_information.append(model_information)

    if agent_registry is not None:
        agent_versions = _get_project_agents_versions(agent_registry)
        for agent_name in agent_versions.keys():
            for version in agent_versions[agent_name]:
                version_name = version["version"]
                agent_information = extract_agent_governance_information(
                    agent_registry, project_name, agent_name, version_name, version.get("creation_timestamp")
                )
                _extract_agent_artifacts(agent_registry, project_name, agent_name, version_name, artifacts_path_tmp)
                project_information.append(agent_information)

    _write_project_information_to_json(
        project_information, os.path.join(artifacts_path_tmp, "project_governance_information.json")
    )
    zip_path = _zip_artifacts_files(
        artifacts_path_tmp, os.path.join(PROJECT_DIR, "tmp", project_name + "_all_governance_artifacts")
    )
    remove_directory(artifacts_path_tmp)
    return zip_path


def return_project_models_governance_information(
    project_name: str, registry: MLFlowModelRegistryAdapter, agent_registry: AgentRegistry | None = None
):
    project_information = []
    versions = _get_project_models_versions(registry)
    for model_name in versions.keys():
        for version in versions[model_name]:
            version_name = version["version"]
            model_information = extract_model_governance_information(registry, project_name, model_name, version_name)
            project_information.append(model_information)

    if agent_registry is not None:
        agent_versions = _get_project_agents_versions(agent_registry)
        for agent_name in agent_versions.keys():
            for version in agent_versions[agent_name]:
                version_name = version["version"]
                agent_information = extract_agent_governance_information(
                    agent_registry, project_name, agent_name, version_name, version.get("creation_timestamp")
                )
                project_information.append(agent_information)

    return project_information


def _write_project_information_to_json(project_information: list, path: str):
    """
    Write the project information to a JSON file
    """
    with open(path, "w") as f:
        json.dump(project_information, f)


def _zip_artifacts_files(folder_to_zip_path: str, zip_destination_path: str):
    """
    Zip the artifacts files
    """
    shutil.make_archive(zip_destination_path, "zip", folder_to_zip_path)
    zip_path = zip_destination_path + ".zip"
    return zip_path


if __name__ == "__main__":
    mlflow_client_manager = MLflowClientManager(tracking_uri="http://model-platform.com/registry/test/")
    mlflow_client_manager.initialize()
    registry_adapter = MLFlowModelRegistryAdapter(mlflow_client_manager=mlflow_client_manager)
    # print(extract_model_governance_information(registry_adapter, "test", "test_model", "3"))
    print(download_project_models_governance_information("test", registry_adapter))
