import re

from kubernetes import client, config
from kubernetes.client import (
    V1HTTPIngressPath,
    V1HTTPIngressRuleValue,
    V1Ingress,
    V1IngressBackend,
    V1IngressRule,
    V1IngressServiceBackend,
    V1IngressSpec,
    V1ServiceBackendPort,
)
from kubernetes.client.rest import ApiException
from loguru import logger

config.load_kube_config()


def sanitize_name(name):
    """Nettoie et format le nom pour être valid dans Kubernetes."""
    sanitized_name = re.sub(r"[^a-z0-9-]", "-", name.lower())
    sanitized_name = re.sub(r"^-+", "", sanitized_name)  # Supprimer tirets au début
    sanitized_name = re.sub(r"-+$", "", sanitized_name)  # Supprimer tirets à la fin
    return sanitized_name


def create_or_update_service(project_name, namespace):
    """Crée ou met à jour un service Kubernetes exposant MLflow."""
    api_instance = client.CoreV1Api()
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=project_name),
        spec=client.V1ServiceSpec(
            selector={"app": project_name},
            ports=[client.V1ServicePort(port=5000, target_port=5000, protocol="TCP", name="http")],
            type="NodePort",
        ),
    )
    try:
        api_instance.read_namespaced_service(project_name, namespace)
        api_instance.replace_namespaced_service(project_name, namespace, service)
        logger.info(f"✅ Service {project_name} successfully updated!")
    except ApiException as e:
        if e.status == 404:
            api_instance.create_namespaced_service(namespace, service)
            logger.info(f"✅ Service {project_name} successfully created!")
        else:
            logger.info(f"⚠️ Error while creating/updating the service: {e}")


def create_or_update_mlflow_deployment(project_name, namespace):
    """Crée ou met à jour un déploiement Kubernetes pour MLflow."""
    api_instance = client.AppsV1Api()

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=project_name),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"app": project_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": project_name}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="mlflow",
                            image="ghcr.io/mlflow/mlflow:v2.9.2",
                            ports=[client.V1ContainerPort(container_port=5000)],
                            env=[
                                client.V1EnvVar(name="MLFLOW_SERVER_HOST", value="0.0.0.0"),
                                client.V1EnvVar(name="MLFLOW_SERVER_PORT", value="5000"),
                                client.V1EnvVar(name="BACKEND_STORE_URI", value="sqlite:///mlflow.db"),
                                client.V1EnvVar(name="ARTIFACT_STORE_URI", value="/mnt/artifacts"),
                            ],
                            command=[
                                "mlflow",
                                "server",
                                "--host",
                                "0.0.0.0",
                                "--port",
                                "5000",
                                "--static-prefix",
                                f"/registry/{project_name}",
                            ],
                        )
                    ]
                ),
            ),
        ),
    )

    try:
        api_instance.read_namespaced_deployment(project_name, namespace)
        api_instance.replace_namespaced_deployment(project_name, namespace, deployment)
        logger.info(f"✅ Deployment {project_name} successfully updated!")
    except ApiException as e:
        if e.status == 404:
            api_instance.create_namespaced_deployment(namespace, deployment)
            logger.info(f"✅ Deployment {project_name} successfully created!")
        else:
            logger.info(f"⚠️ Error while creating/updating the deployment: {e}")


def create_ingres_deployment(ingress_name: str, host: str, project_names_list: list, namespace: str, port: int = 5000):
    api_instance = client.NetworkingV1Api()
    paths = [
        V1HTTPIngressPath(
            path=f"/registry/{project_name}",
            path_type="Prefix",
            backend=V1IngressBackend(
                service=V1IngressServiceBackend(name=project_name, port=V1ServiceBackendPort(number=port))
            ),
        )
        for project_name in project_names_list
    ]

    ingress = V1Ingress(
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata={"name": ingress_name},
        spec=V1IngressSpec(
            ingress_class_name="nginx", rules=[V1IngressRule(host=host, http=V1HTTPIngressRuleValue(paths=paths))]
        ),
    )
    try:
        api_instance.read_namespaced_ingress(ingress_name, namespace)
        api_instance.replace_namespaced_ingress(ingress_name, namespace, ingress)
        logger.info(f"✅ Ingress {host} successfully updated!")
    except ApiException as e:
        if e.status == 404:
            api_instance.create_namespaced_ingress(namespace=namespace, body=ingress)
            logger.info(f"✅ Ingress {host} successfully created!")
        else:
            logger.info(f"⚠️ Error while creating/updating the ingress: {e}")


def add_path_to_ingress(ingress_name: str, host: str, deployment_list: dict, namespace: str, port: int = 5000):
    api_instance = client.NetworkingV1Api()
    existing_ingress = api_instance.read_namespaced_ingress(ingress_name, namespace)
    existing_paths = existing_ingress.spec.rules[0].http.paths if existing_ingress.spec.rules else []
    existing_services = {path.backend.service.name for path in existing_paths}
    new_paths = [
        client.V1HTTPIngressPath(
            path=f"/{path}/{deployment_name}",
            path_type="Prefix",
            backend=client.V1IngressBackend(
                service=client.V1IngressServiceBackend(
                    name=deployment_name, port=client.V1ServiceBackendPort(number=port)
                )
            ),
        )
        for path, deployment_name in deployment_list.items()
        if deployment_name not in existing_services
    ]
    if new_paths:
        existing_paths.extend(new_paths)
        ingress_patch = {"spec": {"rules": [{"host": host, "http": {"paths": existing_paths}}]}}

        api_instance.patch_namespaced_ingress(name=ingress_name, namespace=namespace, body=ingress_patch)
        logger.info(f"✅ Ingress {host} successfully updated with new paths!")
    else:
        logger.info(f"ℹ️ No new paths to add. Ingress {host} remains unchanged.")


def deploy_ingress(project_name, namespace="default"):
    """Déploie MLflow avec un service, un déploiement et un Ingress."""
    logger.info(f"🚀 Deploying MLflow for project: {project_name} in namespace {namespace}")
    create_ingres_deployment("model-platform", "model-platform.com", namespace)
    logger.info("🎉 Deployment completed successfully!")


if __name__ == "__main__":
    project_name = "project-alpha"
    namespace = "default"
    project_name = sanitize_name(project_name)
    project_name = sanitize_name(project_name)
    create_or_update_service(project_name, namespace)
    create_or_update_mlflow_deployment(project_name, namespace)
    create_ingres_deployment("model-platform", "model-platform.com", [project_name], namespace)
    create_or_update_service("project-beta", namespace)
    create_or_update_mlflow_deployment("project-beta", namespace)
    add_path_to_ingress("model-platform", "model-platform.com", {"registry": "project-beta"}, namespace)
