from model_platform.domain.entities.project import Project
from model_platform.domain.ports.project_db_handler import ProjectDbHandler
from model_platform.domain.use_cases.deploy_registry import deploy_registry
from model_platform.infrastructure.k8s_registry_deployment_adapter import K8SRegistryDeployment


def list_projects(project_db_handler: ProjectDbHandler) -> list[dict]:
    projects = project_db_handler.list_projects()
    return [project.to_json() for project in projects]


def undeploy_all_projects_models(project_name: str) -> None:
    pass


def add_project(project_db_handler: ProjectDbHandler, project: Project) -> None:
    project_db_handler.add_project(project)
    deploy_registry(project.name)


def remove_project_namespace(project_name: str) -> None:
    k8s_deployment = K8SRegistryDeployment(project_name)
    k8s_deployment.delete_namespace()


def remove_project(project_db_handler: ProjectDbHandler, project_name: str) -> None:
    project_db_handler.remove_project(project_name)
    remove_project_namespace(project_name)


def get_project_info(project_db_handler: ProjectDbHandler, project_name: str) -> dict:
    project = project_db_handler.get_project(project_name)
    return project.to_json()
