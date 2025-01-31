from kubernetes import client, config, stream

def create_namespace(namespace_name):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_name))
    try:
        v1.create_namespace(body=namespace)
        print(f"Namespace '{namespace_name}' créé avec succès!")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print(f"Namespace '{namespace_name}' existe déjà.")
        else:
            print(f"Erreur lors de la création du namespace: {e}")


def create_deployment(namespace_name, deployment_name, image, container_port):
    apps_v1 = client.AppsV1Api()

    # Définition du déploiement
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"app": deployment_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name=deployment_name,
                            image=image,
                            ports=[client.V1ContainerPort(container_port=container_port)],
                            image_pull_policy="IfNotPresent",
                            env=[
                                client.V1EnvVar(name="MLFLOW_ARTIFACTS_DESTINATION", value="S3://bucket"),
                                client.V1EnvVar(name="MLFLOW_BACKEND_STORE_URI", value="postgresql://user:password@host.docker.internal:5432/mlflowdb")
                            ]
                        )
                    ]
                ),
            ),
        ),
    )
    try:
        apps_v1.create_namespaced_deployment(namespace=namespace_name, body=deployment)
        print(f"Déploiement '{deployment_name}' créé avec succès dans le namespace '{namespace_name}'!")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print(f"Déploiement '{deployment_name}' existe déjà, mise à jour en cours...")
            apps_v1.replace_namespaced_deployment(name=deployment_name, namespace=namespace_name, body=deployment)
            print(f"Déploiement '{deployment_name}' mis à jour avec succès!")
        else:
            print(f"Erreur lors de la création du déploiement: {e}")


def create_service(namespace_name, service_name, deployment_name, service_port, target_port):
    v1 = client.CoreV1Api()

    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=service_name),
        spec=client.V1ServiceSpec(
            type="NodePort" ,
            selector={"app": deployment_name}, 
            ports=[client.V1ServicePort(port=service_port, target_port=target_port)]
        ),
    )
    try:
        v1.create_namespaced_service(namespace=namespace_name, body=service)
        print(f"Service '{service_name}' créé avec succès dans le namespace '{namespace_name}'!")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print(f"Service '{service_name}' existe déjà, mise à jour en cours...")
            v1.replace_namespaced_service(name=service_name, namespace=namespace_name, body=service)
            print(f"Déploiement '{deployment_name}' mis à jour avec succès!")
        else:
            print(f"Erreur lors de la création du service: {e}")


if __name__ == "__main__":
    # Paramètres
    namespace_name = "mlflow-namespace"
    deployment_name = "mlflow-deployment"
    service_name = "mlflow-service"
    image = "model-registry"  # Utilisez l'image officielle MLflow
    container_port = 5000
    service_port = 5000  # Port du service ClusterIP exposé aux autres applications du cluster kube
    target_port = 5000  # Port interne du conteneur
    localhost_port = '8080'

    # # Création des resources
    create_namespace(namespace_name)
    create_deployment(namespace_name, deployment_name, image, container_port)
    create_service(namespace_name, service_name, deployment_name, service_port, target_port)
