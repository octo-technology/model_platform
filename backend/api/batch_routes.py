# Philippe Stepniewski
import inspect
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from loguru import logger
from starlette.responses import JSONResponse, Response

from backend.domain.entities.batch_prediction import BatchPredictionStatus
from backend.domain.ports.batch_prediction_handler import BatchPredictionHandler
from backend.domain.ports.object_storage_handler import ObjectStorageHandler
from backend.domain.ports.project_db_handler import ProjectDbHandler
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.batch_predict import (
    cleanup_batch_predictions,
    delete_batch_prediction,
    download_batch_result,
    get_batch_prediction_status,
    list_batch_predictions,
    submit_batch_prediction,
)
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project
from backend.utils import sanitize_project_name

router = APIRouter()


def get_batch_handler(request: Request) -> BatchPredictionHandler:
    return request.app.state.batch_handler


def get_project_db_handler(request: Request) -> ProjectDbHandler:
    return request.app.state.project_db_handler


def get_object_storage_handler(request: Request) -> ObjectStorageHandler:
    return request.app.state.object_storage_handler


def get_registry_pool(request: Request) -> RegistryHandler:
    return request.app.state.registry_pool


def get_tasks_status(request: Request) -> dict:
    return request.app.state.task_status


def _get_project_registry_tracking_uri(project_name: str) -> str:
    sanitized = sanitize_project_name(project_name)
    return f"http://{sanitized}.{sanitized}.svc.cluster.local:5000"


def _run_batch_submission(
    tasks_status: dict,
    job_id: str,
    registry,
    project_name: str,
    model_name: str,
    version: str,
    file_content: bytes,
    object_storage: ObjectStorageHandler,
    batch_handler: BatchPredictionHandler,
    project_db_handler: ProjectDbHandler,
):
    try:
        tasks_status[job_id] = BatchPredictionStatus.BUILDING.value
        submit_batch_prediction(
            project_name=project_name,
            model_name=model_name,
            version=version,
            file_content=file_content,
            job_id=job_id,
            object_storage=object_storage,
            batch_handler=batch_handler,
            project_db_handler=project_db_handler,
            registry=registry,
        )
        del tasks_status[job_id]
    except Exception as e:
        logger.error(f"Batch submission failed for job {job_id}: {e}")
        tasks_status[job_id] = BatchPredictionStatus.FAILED.value


@router.post("/submit/{model_name}/{version}")
async def route_submit_batch(
    project_name: str,
    model_name: str,
    version: str,
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    batch_handler: BatchPredictionHandler = Depends(get_batch_handler),
    object_storage: ObjectStorageHandler = Depends(get_object_storage_handler),
    project_db_handler: ProjectDbHandler = Depends(get_project_db_handler),
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    tasks_status: dict = Depends(get_tasks_status),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    file_content = await file.read()

    registry = registry_pool.get_registry_adapter(project_name, _get_project_registry_tracking_uri(project_name))

    job_id = str(uuid.uuid4())[:8]
    tasks_status[job_id] = BatchPredictionStatus.BUILDING.value

    background_tasks.add_task(
        _run_batch_submission,
        tasks_status,
        job_id,
        registry,
        project_name,
        model_name,
        version,
        file_content,
        object_storage,
        batch_handler,
        project_db_handler,
    )

    return JSONResponse(
        content={"job_id": job_id, "status": BatchPredictionStatus.BUILDING.value},
        media_type="application/json",
    )


@router.get("/status/{job_id}")
def route_batch_status(
    project_name: str,
    job_id: str,
    batch_handler: BatchPredictionHandler = Depends(get_batch_handler),
    tasks_status: dict = Depends(get_tasks_status),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    # Check if the job is still in the build phase (tracked in-memory)
    if job_id in tasks_status:
        status = tasks_status[job_id]
        if status == BatchPredictionStatus.BUILDING.value:
            return JSONResponse(
                content={"job_id": job_id, "status": BatchPredictionStatus.BUILDING.value},
                media_type="application/json",
            )
        if status == BatchPredictionStatus.FAILED.value:
            return JSONResponse(
                content={"job_id": job_id, "status": BatchPredictionStatus.FAILED.value},
                media_type="application/json",
            )

    result = get_batch_prediction_status(project_name, job_id, batch_handler)
    return JSONResponse(content=result, media_type="application/json")


@router.get("/list")
def route_list_batch(
    project_name: str,
    batch_handler: BatchPredictionHandler = Depends(get_batch_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    result = list_batch_predictions(project_name, batch_handler)
    return JSONResponse(content=result, media_type="application/json")


@router.get("/download/{job_id}")
def route_download_batch(
    project_name: str,
    job_id: str,
    batch_handler: BatchPredictionHandler = Depends(get_batch_handler),
    object_storage: ObjectStorageHandler = Depends(get_object_storage_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    try:
        content = download_batch_result(project_name, job_id, batch_handler, object_storage)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=predictions-{job_id}.csv"},
        )
    except Exception as e:
        logger.error(f"Failed to download batch result: {e}")
        raise HTTPException(status_code=404, detail="Batch result not found or not yet available")


@router.delete("/{job_id}")
def route_delete_batch(
    project_name: str,
    job_id: str,
    batch_handler: BatchPredictionHandler = Depends(get_batch_handler),
    object_storage: ObjectStorageHandler = Depends(get_object_storage_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    result = delete_batch_prediction(project_name, job_id, batch_handler, object_storage)
    return JSONResponse(content={"status": result}, media_type="application/json")


@router.post("/cleanup")
def route_cleanup_batch(
    project_name: str,
    batch_handler: BatchPredictionHandler = Depends(get_batch_handler),
    object_storage: ObjectStorageHandler = Depends(get_object_storage_handler),
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    deleted_count = cleanup_batch_predictions(project_name, batch_handler, object_storage)
    return JSONResponse(content={"deleted": deleted_count}, media_type="application/json")
