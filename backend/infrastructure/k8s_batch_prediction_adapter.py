# Philippe Stepniewski
from datetime import datetime, timezone

from kubernetes import client
from kubernetes.client.rest import ApiException
from loguru import logger

from backend.domain.entities.batch_prediction import BatchPrediction, BatchPredictionStatus
from backend.domain.ports.batch_prediction_handler import BatchPredictionHandler
from backend.infrastructure.k8s_deployment import K8SDeployment
from backend.utils import sanitize_project_name


class K8sBatchPredictionAdapter(BatchPredictionHandler, K8SDeployment):
    def __init__(self):
        super().__init__()
        self.batch_api = client.BatchV1Api()

    def create_batch_job(
        self, project_name: str, model_name: str, model_version: str, input_path: str, output_path: str, job_id: str
    ) -> BatchPrediction:
        namespace = sanitize_project_name(project_name)
        docker_image_name = sanitize_project_name(f"{project_name}_{model_name}_{model_version}_ctr")

        env_vars = [
            client.V1EnvVar(name="INPUT_PATH", value=input_path),
            client.V1EnvVar(name="OUTPUT_PATH", value=output_path),
            client.V1EnvVar(name="BATCH_BUCKET", value="batch-predictions"),
            client.V1EnvVar(name="MLFLOW_S3_ENDPOINT_URL", value=self._get_env("MLFLOW_S3_ENDPOINT_URL")),
            client.V1EnvVar(name="AWS_ACCESS_KEY_ID", value=self._get_env("AWS_ACCESS_KEY_ID", "minio_user")),
            client.V1EnvVar(
                name="AWS_SECRET_ACCESS_KEY", value=self._get_env("AWS_SECRET_ACCESS_KEY", "minio_password")
            ),
        ]

        job = client.V1Job(
            metadata=client.V1ObjectMeta(
                name=f"batch-{job_id}",
                namespace=namespace,
                labels={
                    "app": "batch-prediction",
                    "project": sanitize_project_name(project_name),
                    "model": sanitize_project_name(model_name),
                    "version": sanitize_project_name(model_version),
                    "model-raw": model_name,
                    "version-raw": model_version,
                    "job_id": job_id,
                },
            ),
            spec=client.V1JobSpec(
                backoff_limit=1,
                ttl_seconds_after_finished=3600,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "app": "batch-prediction",
                            "job_id": job_id,
                        }
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="batch-predict",
                                image=f"{docker_image_name}:latest",
                                image_pull_policy="IfNotPresent",
                                command=["bash", "-c", "uv run python batch_predict_template.py"],
                                env=env_vars,
                            )
                        ],
                        restart_policy="Never",
                    ),
                ),
            ),
        )

        self.batch_api.create_namespaced_job(namespace=namespace, body=job)
        logger.info(f"Created batch job batch-{job_id} in namespace {namespace}")

        return BatchPrediction(
            job_id=job_id,
            project_name=project_name,
            model_name=model_name,
            model_version=model_version,
            status=BatchPredictionStatus.PENDING,
            input_path=input_path,
            output_path=output_path,
            created_at=datetime.now(timezone.utc),
        )

    def get_job_status(self, project_name: str, job_id: str) -> BatchPrediction:
        namespace = sanitize_project_name(project_name)
        job = self.batch_api.read_namespaced_job(name=f"batch-{job_id}", namespace=namespace)
        return self._job_to_batch_prediction(job)

    def list_batch_jobs(self, project_name: str) -> list[BatchPrediction]:
        namespace = sanitize_project_name(project_name)
        jobs = self.batch_api.list_namespaced_job(namespace=namespace, label_selector="app=batch-prediction")
        return [self._job_to_batch_prediction(job) for job in jobs.items]

    def delete_batch_job(self, project_name: str, job_id: str) -> bool:
        namespace = sanitize_project_name(project_name)
        try:
            self.batch_api.delete_namespaced_job(
                name=f"batch-{job_id}",
                namespace=namespace,
                body=client.V1DeleteOptions(propagation_policy="Background"),
            )
            logger.info(f"Deleted batch job batch-{job_id} from namespace {namespace}")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Batch job batch-{job_id} not found in namespace {namespace}")
                return False
            raise

    def list_finished_jobs(self, project_name: str) -> list[BatchPrediction]:
        namespace = sanitize_project_name(project_name)
        jobs = self.batch_api.list_namespaced_job(namespace=namespace, label_selector="app=batch-prediction")
        finished = []
        for job in jobs.items:
            bp = self._job_to_batch_prediction(job)
            if bp.status in (BatchPredictionStatus.COMPLETED, BatchPredictionStatus.FAILED):
                finished.append(bp)
        return finished

    def _job_to_batch_prediction(self, job: client.V1Job) -> BatchPrediction:
        labels = job.metadata.labels or {}
        status = self._map_job_status(job.status)

        started_at = None
        completed_at = None
        error_message = None

        if job.status.start_time:
            started_at = job.status.start_time

        if job.status.completion_time:
            completed_at = job.status.completion_time

        if status == BatchPredictionStatus.FAILED:
            error_message = self._get_pod_error_logs(job.metadata.namespace, job.metadata.name)

        env_vars = {}
        containers = job.spec.template.spec.containers
        if containers:
            for env in containers[0].env or []:
                env_vars[env.name] = env.value

        return BatchPrediction(
            job_id=labels.get("job_id", ""),
            project_name=labels.get("project", ""),
            model_name=labels.get("model-raw", labels.get("model", "")),
            model_version=labels.get("version-raw", labels.get("version", "")),
            status=status,
            input_path=env_vars.get("INPUT_PATH", ""),
            output_path=env_vars.get("OUTPUT_PATH", ""),
            created_at=job.metadata.creation_timestamp or datetime.now(timezone.utc),
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
        )

    def _map_job_status(self, status: client.V1JobStatus) -> BatchPredictionStatus:
        if status.succeeded and status.succeeded > 0:
            return BatchPredictionStatus.COMPLETED
        if status.failed and status.failed > 0:
            return BatchPredictionStatus.FAILED
        if status.active and status.active > 0:
            return BatchPredictionStatus.RUNNING
        return BatchPredictionStatus.PENDING

    def _get_pod_error_logs(self, namespace: str, job_name: str) -> str:
        try:
            pods = self.service_api_instance.list_namespaced_pod(
                namespace=namespace, label_selector=f"job-name={job_name}"
            )
            if not pods.items:
                return "No pod found for this job"
            pod = pods.items[0]
            logs = self.service_api_instance.read_namespaced_pod_log(
                name=pod.metadata.name, namespace=namespace, tail_lines=30
            )
            lines = [line for line in logs.strip().splitlines() if line.strip()]
            if not lines:
                return "No logs available"
            return "\n".join(lines[-5:])
        except Exception as e:
            logger.warning(f"Could not fetch pod logs for job {job_name}: {e}")
            return "Could not retrieve error details"

    def _get_env(self, key: str, default: str = "") -> str:
        import os

        return os.environ.get(key, default)
