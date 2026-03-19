# Philippe Stepniewski
from fastapi import HTTPException
from loguru import logger

from backend.domain.entities.docker.utils import build_model_docker_image, check_docker_image_exists, sanitize_name
from backend.domain.ports.batch_prediction_handler import BatchPredictionHandler
from backend.domain.ports.object_storage_handler import ObjectStorageHandler
from backend.domain.ports.project_db_handler import ProjectDbHandler


def ensure_model_image_exists(registry, project_name: str, model_name: str, version: str):
    image_name = sanitize_name(f"{project_name}_{model_name}_{version}_ctr")
    if check_docker_image_exists(image_name):
        logger.info(f"Docker image '{image_name}' already exists, skipping build")
        return
    logger.info(f"Docker image '{image_name}' not found, building...")
    build_status = build_model_docker_image(registry, project_name, model_name, version)
    if build_status == 0:
        raise HTTPException(status_code=500, detail="Failed to build model image")
    logger.info(f"Docker image '{image_name}' built successfully")


def submit_batch_prediction(
    project_name: str,
    model_name: str,
    version: str,
    file_content: bytes,
    job_id: str,
    object_storage: ObjectStorageHandler,
    batch_handler: BatchPredictionHandler,
    project_db_handler: ProjectDbHandler,
    registry=None,
):
    project = project_db_handler.get_project(project_name)
    if not project.batch_enabled:
        raise HTTPException(status_code=400, detail="Batch predictions are not enabled for this project")

    input_path = f"{project_name}/{model_name}/{version}/{job_id}/input.csv"
    output_path = f"{project_name}/{model_name}/{version}/{job_id}/predictions-{job_id}.csv"

    logger.info(f"Uploading input file to {input_path}")
    object_storage.upload_file(project_name, f"{model_name}/{version}/{job_id}/input.csv", file_content)

    if registry:
        ensure_model_image_exists(registry, project_name, model_name, version)

    batch_prediction = batch_handler.create_batch_job(
        project_name, model_name, version, input_path, output_path, job_id
    )
    return batch_prediction.to_json()


def get_batch_prediction_status(project_name: str, job_id: str, batch_handler: BatchPredictionHandler):
    batch_prediction = batch_handler.get_job_status(project_name, job_id)
    return batch_prediction.to_json()


def list_batch_predictions(project_name: str, batch_handler: BatchPredictionHandler):
    jobs = batch_handler.list_batch_jobs(project_name)
    return [job.to_json() for job in jobs]


def download_batch_result(
    project_name: str,
    job_id: str,
    batch_handler: BatchPredictionHandler,
    object_storage: ObjectStorageHandler,
):
    batch_prediction = batch_handler.get_job_status(project_name, job_id)
    model = batch_prediction.model_name
    version = batch_prediction.model_version
    output_remote_path = f"{model}/{version}/{job_id}/predictions-{job_id}.csv"
    content = object_storage.download_file(project_name, output_remote_path)
    return content


def delete_batch_prediction(
    project_name: str,
    job_id: str,
    batch_handler: BatchPredictionHandler,
    object_storage: ObjectStorageHandler,
):
    batch_prediction = batch_handler.get_job_status(project_name, job_id)
    model_name = batch_prediction.model_name
    model_version = batch_prediction.model_version

    batch_handler.delete_batch_job(project_name, job_id)

    prefix = f"{model_name}/{model_version}/{job_id}/"
    files = object_storage.list_files(project_name, prefix)
    for f in files:
        object_storage.delete_file(project_name, f)

    logger.info(f"Deleted batch prediction {job_id} and associated files")
    return True


def cleanup_batch_predictions(
    project_name: str,
    batch_handler: BatchPredictionHandler,
    object_storage: ObjectStorageHandler,
):
    finished_jobs = batch_handler.list_finished_jobs(project_name)
    deleted_count = 0
    for job in finished_jobs:
        job_id = job.job_id
        batch_handler.delete_batch_job(project_name, job_id)

        prefix = f"{job.model_name}/{job.model_version}/{job_id}/"
        files = object_storage.list_files(project_name, prefix)
        for f in files:
            object_storage.delete_file(project_name, f)

        deleted_count += 1
        logger.info(f"Cleaned up batch job {job_id} ({job.status.value})")

    logger.info(f"Cleaned up {deleted_count} finished batch jobs for project {project_name}")
    return deleted_count
