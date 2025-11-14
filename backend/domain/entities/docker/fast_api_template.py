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
from pydantic import BaseModel

try:
    logger.info("Starting up and loading model...")
    model = mlflow.pyfunc.load_model("/opt/mlflow/")
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")

image_name = os.environ["IMAGE_NAME"]

tracer = trace.get_tracer(f"model_platform_{image_name}")

app = FastAPI(reload=True)


class PredictionRequest(BaseModel):
    inputs: Dict[str, Any]


class PredictionResponse(BaseModel):
    outputs: Any


@app.post("/predict", response_model=PredictionResponse)
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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics_endpoint():
    return Response(content=generate_latest(), media_type="text/plain")


FastAPIInstrumentor.instrument_app(app)

# OpenTelemetry setup
base_resource = Resource.create()
service_resource = Resource.create({SERVICE_NAME: f"model-platform-{image_name}"})
resource = base_resource.merge(service_resource)

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
