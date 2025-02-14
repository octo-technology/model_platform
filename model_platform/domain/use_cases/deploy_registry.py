from model_platform.infrastructure.k8s_registry_deployment_adapter import K8SRegistryDeployment


def deploy_registry(project_name: str) -> None:
    k8s_deployment = K8SRegistryDeployment(project_name)
    k8s_deployment.create_registry_deployment()
