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
                            args=["--backend-store-uri", "postgresql://user:password@127.0.0.1:5432/mlflowdb"]
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

def get_mlflow_tracking_server_uri(localhost_port):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # # get nodePort
    # node_ports = svc.spec.ports[0].node_port

    svc = v1.read_namespaced_service(namespace=namespace_name, name=service_name)
    selector = svc.spec.selector

    if not selector:
        raise Exception(f"Le service '{service_name}' n'a pas de selector !")

    # Transformer le selector en format "key1=value1,key2=value2"
    selector_str = ",".join([f"{k}={v}" for k, v in selector.items()])

    # Récupérer les pods correspondant
    pods = v1.list_namespaced_pod(namespace=namespace_name, label_selector=selector_str).items

    if not pods:
        print(f"Aucun pod trouvé pour le service '{service_name}'")

    pod_name = pods[0].metadata.name

    # Ouvrir un tunnel de port-forwarding
    try:
        pf = stream.portforward(v1.connect_get_namespaced_pod_portforward, pod_name, namespace_name, ports=localhost_port)
    except Exception as e:
        raise e 

    print(f"Port-forwarding ouvert sur http://localhost:{localhost_port} -> {pod_name}:{container_port}")

    import requests
    r = requests.get(f"http://localhost:{localhost_port}")
    print(r.status_code)
    


if __name__ == "__main__":
    # Paramètres
    namespace_name = "mlflow-namespace"
    deployment_name = "mlflow-deployment"
    service_name = "mlflow-service"
    image = "model-registry"  # Utilisez l'image officielle MLflow
    container_port = 5000
    service_port = 5000  # Port du service ClusterIP exposé aux autres applications du cluster kube
    target_port = 5000  # Port interne du conteneur
    localhost_port = '80'

    # Création des resources
    # create_namespace(namespace_name)
    # create_deployment(namespace_name, deployment_name, image, container_port, project_name)
    # create_service(namespace_name, service_name, deployment_name, service_port, target_port)
    get_mlflow_tracking_server_uri(localhost_port)
