import os
from typing import Any, Dict, Optional

import mlflow
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from loguru import logger
from opentelemetry import metrics, trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from prometheus_client import generate_latest
from pydantic import BaseModel, create_model

try:
    logger.info("Starting up and loading model...")
    model = mlflow.pyfunc.load_model("/opt/mlflow/")
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    model = None

image_name = os.environ["IMAGE_NAME"]

tracer = trace.get_tracer(f"model_platform_{image_name}")

# ---------------------------------------------------------------------------
# Dynamic schema discovery from MLflow model signature
# ---------------------------------------------------------------------------
MLFLOW_TYPE_MAP = {
    "double": float,
    "float": float,
    "long": int,
    "integer": int,
    "string": str,
    "boolean": bool,
}

DynamicInputs = None
DynamicOutputs = None
signature_description = ""

try:
    if model is not None and hasattr(model, "metadata") and model.metadata and model.metadata.signature:
        sig = model.metadata.signature

        # Build input schema
        if sig.inputs and hasattr(sig.inputs, "inputs") and sig.inputs.inputs:
            fields = {}
            field_descriptions = []
            for col in sig.inputs.inputs:
                col_type_str = str(col.type)
                py_type = MLFLOW_TYPE_MAP.get(col_type_str, Any)
                fields[col.name] = (py_type, ...)
                field_descriptions.append(f"- **{col.name}**: `{col_type_str}`")
            if fields:
                DynamicInputs = create_model("ModelInputs", **fields)
                signature_description = "### Input schema (from MLflow signature)\n" + "\n".join(field_descriptions)
                logger.info(f"Built dynamic input schema with {len(fields)} fields: {list(fields.keys())}")

        # Build output schema (best-effort, less critical)
        if sig.outputs and hasattr(sig.outputs, "inputs") and sig.outputs.inputs:
            out_fields = {}
            for col in sig.outputs.inputs:
                col_type_str = str(col.type)
                py_type = MLFLOW_TYPE_MAP.get(col_type_str, Any)
                out_fields[col.name] = (py_type, ...)
            if out_fields:
                DynamicOutputs = create_model("ModelOutputs", **out_fields)
                logger.info(f"Built dynamic output schema with {len(out_fields)} fields: {list(out_fields.keys())}")

except Exception as e:
    logger.warning(f"Could not build dynamic schema from model signature, falling back to generic schema: {e}")
    DynamicInputs = None
    DynamicOutputs = None
    signature_description = ""

# ---------------------------------------------------------------------------
# Request / Response models (dynamic if signature available, generic fallback)
# ---------------------------------------------------------------------------
if DynamicInputs is not None:

    class PredictionRequest(BaseModel):
        inputs: DynamicInputs

else:

    class PredictionRequest(BaseModel):
        inputs: Dict[str, Any]


class PredictionResponse(BaseModel):
    outputs: Any


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
api_description = f"""Inference API for deployed ML model **{image_name}**.

Accepts JSON payloads or file uploads for prediction.

{signature_description}
"""

app = FastAPI(
    title=f"Model API - {image_name}",
    description=api_description,
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
)


@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Run inference",
    description="Send input features as JSON or upload a file for prediction.",
)
async def predict(request: Request, file: Optional[UploadFile] = File(None)):
    tracer = trace.get_tracer(__name__)
    try:
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            if not file:
                raise HTTPException(status_code=400, detail="No file uploaded")
            contents = await file.read()
            logger.info("Received file for inference")
            with tracer.start_as_current_span("model_inference"):
                model_predict = model.predict(contents)

        elif "application/json" in content_type:
            body = await request.json()
            payload = PredictionRequest(**body)
            input_data = payload.inputs
            logger.info("Received JSON data for inference")

            if isinstance(input_data, dict):
                input_df = pd.DataFrame([input_data])
            elif isinstance(input_data, BaseModel):
                input_df = pd.DataFrame([input_data.model_dump()])
            else:
                input_df = pd.DataFrame(input_data)

            with tracer.start_as_current_span("model_inference"):
                model_predict = model.predict(input_df)

        else:
            raise HTTPException(status_code=400, detail="Unsupported content type")

        if isinstance(model_predict, np.ndarray):
            model_predict = model_predict.tolist()

        return PredictionResponse(outputs=model_predict)

    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", summary="Health check")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics", summary="Prometheus metrics")
def metrics_endpoint():
    return Response(content=generate_latest(), media_type="text/plain")


FastAPIInstrumentor.instrument_app(app)
# Check si on devrait mettre le service name lie a k8s
resource = Resource.create(attributes={SERVICE_NAME: f"model-platform-{image_name}"})

# Prometheus client
reader = PrometheusMetricReader()
metric_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(metric_provider)

# Tracer exporter
zipkin_endpoint = os.getenv("ZIPKIN_ENDPOINT")
if zipkin_endpoint:
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    zipkin_exporter = ZipkinExporter(endpoint=zipkin_endpoint)
    trace_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(zipkin_exporter)
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)
