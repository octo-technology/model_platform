import os

from kubernetes import client, config
from kubernetes.client import AppsV1Api, CoreV1Api
from kubernetes.client.rest import ApiException
from loguru import logger

from model_platform.domain.ports.registry_deployment_handler import RegistryDeployment
from model_platform.infrastructure.k8s_deployment import K8SDeployment
from model_platform.utils import sanitize_name


class K8SRegistryDeployment(RegistryDeployment, K8SDeployment):

    def __init__(self, project_name: str):
        super().__init__()
        config.load_kube_config()
        self.service_api_instance: CoreV1Api = client.CoreV1Api()
        self.apps_api_instance: AppsV1Api = client.AppsV1Api()
        self.host_name = os.environ["MP_HOST_NAME"]
        self.sub_path = os.environ["MP_REGISTRY_PATH"]
        self.port = int(os.environ["MP_REGISTRY_PORT"])
        self.namespace = sanitize_name(project_name)
        self.project_name = sanitize_name(project_name)
        self.pgsql_password = os.environ["POSTGRES_PASSWORD"]
        self.pgsql_user = os.environ["POSTGRES_USER"]
        self.local_ip = os.environ["LOCAL_IP"]
        self.pgsql_cluster_host = (
            f"{os.environ['PGSQL_HOST']}-postgresql.{os.environ['PGSQL_NAMESPACE']}.svc.cluster.local"
        )
        self.mlflow_db_name = self.project_name

    def create_registry_deployment(self):
        self._create_or_update_namespace()
        self._create_or_update_service(self.project_name)
        self._create_or_update_mlflow_deployment(self.project_name)

    def _create_or_update_service(self, project_name: str):
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=project_name),
            spec=client.V1ServiceSpec(
                selector={"app": project_name},
                ports=[client.V1ServicePort(port=self.port, target_port=self.port, protocol="TCP", name="http")],
                type="NodePort",
            ),
        )
        try:
            self.service_api_instance.read_namespaced_service(project_name, self.namespace)
            self.service_api_instance.replace_namespaced_service(project_name, self.namespace, service)
            logger.info(f"✅ Service {project_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                self.service_api_instance.create_namespaced_service(self.namespace, service)
                logger.info(f"✅ Service {project_name} successfully created!")
            else:
                logger.info(f"⚠️ Error while creating/updating the service: {e}")

    def _create_or_update_mlflow_deployment(self, project_name: str):
        """Crée ou met à jour un déploiement Kubernetes pour MLflow."""
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=project_name, labels={"project_name": self.project_name, "type": "model_registry"}
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": project_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": project_name}),
                    spec=client.V1PodSpec(
                        init_containers=[
                            client.V1Container(
                                name="init-db",
                                image="postgres:13",
                                command=[
                                    "sh",
                                    "-c",
                                    f"psql -h {self.pgsql_cluster_host} -U {self.pgsql_user} -d postgres -tc \"SELECT 1 FROM pg_database WHERE datname = '{self.mlflow_db_name}';\" | grep -q 1 || psql -h {self.pgsql_cluster_host} -U {self.pgsql_user} -d postgres -c 'CREATE DATABASE {self.mlflow_db_name};'",
                                ],
                                env=[
                                    client.V1EnvVar(name="PGPASSWORD", value=self.pgsql_password),
                                ],
                            )
                        ],
                        containers=[
                            client.V1Container(
                                name="mlflow",
                                # image="ghcr.io/mlflow/mlflow:v2.9.2",
                                image="mlflow:latest",
                                image_pull_policy="IfNotPresent",
                                ports=[client.V1ContainerPort(container_port=self.port)],
                                env=[
                                    client.V1EnvVar(name="MLFLOW_SERVER_HOST", value="0.0.0.0"),
                                    client.V1EnvVar(name="MLFLOW_SERVER_PORT", value=str(self.port)),
                                    client.V1EnvVar(name="AWS_ACCESS_KEY_ID", value="minio_user"),
                                    client.V1EnvVar(name="AWS_SECRET_ACCESS_KEY", value="minio_password"),
                                    client.V1EnvVar(
                                        name="MLFLOW_S3_ENDPOINT_URL", value=f"http://{self.local_ip}:9000"
                                    ),
                                ],
                                command=[
                                    "mlflow",
                                    "server",
                                    "--host",
                                    "0.0.0.0",
                                    "--port",
                                    str(self.port),
                                    "--backend-store-uri",
                                    f"postgresql://{self.pgsql_user}:{self.pgsql_password}@{self.pgsql_cluster_host}/{self.mlflow_db_name}",
                                    "--artifacts-destination",
                                    "s3://bucket",
                                    #  "--static-prefix",
                                    #  f"/{self.sub_path}/{project_name}",
                                ],
                                lifecycle=client.V1Lifecycle(
                                    pre_stop=client.V1LifecycleHandler(
                                        _exec=client.V1ExecAction(
                                            command=[
                                                "sh",
                                                "-c",
                                                f'psql -h {self.pgsql_cluster_host} -U {self.pgsql_user} -d postgres -tc "DROP DATABASE IF EXISTS {self.mlflow_db_name};" ',
                                            ],
                                        )
                                    )
                                ),
                            )
                        ],
                    ),
                ),
            ),
        )

        try:
            self.apps_api_instance.read_namespaced_deployment(project_name, self.namespace)
            self.apps_api_instance.replace_namespaced_deployment(project_name, self.namespace, deployment)
            logger.info(f"✅ Deployment {project_name} successfully updated!")
        except ApiException as e:
            if e.status == 404:
                self.apps_api_instance.create_namespaced_deployment(self.namespace, deployment)
                logger.info(f"✅ Deployment {project_name} successfully created!")
            else:
                logger.info(f"⚠️ Error while creating/updating the deployment: {e}")

    def create_db_dropper_job(self):
        logger.info(f"Creating job to drop database {self.mlflow_db_name}...")
        batch_api_instance = client.BatchV1Api()
        job_name = "drop-db-job"
        try:
            logger.info("Checking if job already exists...")
            batch_api_instance.read_namespaced_job(name=job_name, namespace="pgsql")
            batch_api_instance.delete_namespaced_job(
                name=job_name, namespace="pgsql", body=client.V1DeleteOptions(propagation_policy="Foreground")
            )
            logger.info(f"ℹ️ Job {job_name} existent supprimé avant recréation.")
        except ApiException as e:
            if e.status != 404:
                logger.error(f"⚠️ Erreur en vérifiant/supprimant le job existent {job_name}: {e}")
                return

        container = client.V1Container(
            name="drop-db-container",
            image="postgres:latest",
            command=[
                "/bin/sh",
                "-c",
                f"PGPASSWORD=$PGPASSWORD psql -h {self.pgsql_cluster_host} -U {self.pgsql_user} -c 'DROP DATABASE IF EXISTS {self.mlflow_db_name};'",
            ],
            env=[client.V1EnvVar(name="PGPASSWORD", value=self.pgsql_password)],
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"job-name": job_name}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container]),
        )

        job_spec = client.V1JobSpec(template=template, backoff_limit=4, ttl_seconds_after_finished=30)

        job = client.V1Job(metadata=client.V1ObjectMeta(name=job_name), spec=job_spec)

        try:
            batch_api_instance.create_namespaced_job(namespace="pgsql", body=job)
            logger.info(f"✅ Job {job_name} created to drop database {self.mlflow_db_name}.")
        except ApiException as e:
            logger.error(f"⚠️ Error while creating job {job_name}: {e}")
