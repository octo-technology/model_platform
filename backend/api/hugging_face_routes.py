import inspect
import uuid

import mlflow.pyfunc
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from huggingface_hub.errors import HfHubHTTPError
from loguru import logger
from starlette.responses import JSONResponse
from transformers import pipeline

from backend.api.models_routes import (
    get_project_registry_tracking_uri,
    get_registry_pool,
    get_tasks_status,
    track_task_status,
)
from backend.domain.ports.model_registry import ModelRegistry
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.ports.user_handler import UserHandler
from backend.domain.use_cases.auth_usecases import get_current_user, get_user_adapter
from backend.domain.use_cases.user_usecases import user_can_perform_action_for_project

router = APIRouter()


@router.get("/search")
def search_models(
    search_args: str,
    max_responses: int = 10,
    _=Depends(get_current_user),
) -> JSONResponse:
    from huggingface_hub import HfApi

    api = HfApi()
    try:
        models = api.list_models(search=search_args)
        result = []
        for model in models:
            result.append(
                {
                    "name": model.id,
                    "creation_date": model.created_at.isoformat(),
                    "version": 1,
                    "aliases": {"tags": model.pipeline_tag},
                }
            )
            if len(result) >= max_responses:
                break
    except HfHubHTTPError:
        return JSONResponse("hf_timeout", status_code=504)
    return JSONResponse(result, media_type="application/json")


@router.get("/get_model")
def get_model(
    project_name: str,
    model_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    tasks_status: dict = Depends(get_tasks_status),
    current_user: dict = Depends(get_current_user),
    user_adapter: UserHandler = Depends(get_user_adapter),
) -> JSONResponse:
    logger.info("Got get call")

    registry: ModelRegistry = registry_pool.get_registry_adapter(
        project_name, get_project_registry_tracking_uri(project_name, request)
    )
    user_can_perform_action_for_project(
        current_user,
        project_name=project_name,
        action_name=inspect.currentframe().f_code.co_name,
        user_adapter=user_adapter,
    )
    task_id = str(uuid.uuid4())
    tasks_status[task_id] = "queued"
    decorated_task = track_task_status(task_id, tasks_status)(log_model_task)
    background_tasks.add_task(decorated_task, registry, model_id)

    return JSONResponse({"task_id": task_id, "status": "Get model initiated"}, media_type="application/json")


def log_model_task(registry, model_id):
    class HFModelWrapper(mlflow.pyfunc.PythonModel):
        def load_context(self, context):
            self.model = pipeline(model_id, model=model_id)

        def predict(self, model_input):
            if isinstance(model_input, dict):
                input_df = pd.DataFrame([model_input])
            else:
                input_df = pd.DataFrame(model_input)
            return self.model(input_df.iloc[:, 0].tolist())

    try:
        model_name = model_id.split("/")[-1]
        registry.log_model(
            python_model=HFModelWrapper(), artifact_path="custom_model", registered_model_name=f"hf_{model_name}"
        )
    except Exception as e:
        logger.error(e)
    logger.info("Finished logging model")
