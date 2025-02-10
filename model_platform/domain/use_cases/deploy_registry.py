from model_platform.infrastructure.k8s_registry_deployment_adapter import K8SDeployment


def deploy_registry(project_name: str) -> None:
    k8s_deployment = K8SDeployment()
    k8s_deployment.create_deployment(project_name)
