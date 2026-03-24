import atexit
import os
from typing import Any, Dict, Optional

import mlflow
import numpy as np
import pandas as pd
from codecarbon import OfflineEmissionsTracker
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from loguru import logger
from opentelemetry import metrics, trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from prometheus_client import Counter, generate_latest
from pydantic import BaseModel

try:
    logger.info("Starting up and loading model...")
    model = mlflow.pyfunc.load_model("/opt/mlflow/")
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")

image_name = os.environ["IMAGE_NAME"]

# --- Carbon footprint tracking (CodeCarbon, background, every 15s) ---
co2_counter = Counter(
    "model_co2_emissions_mg_total",
    "Cumulative CO2 equivalent emissions in milligrams (CodeCarbon, country: FRA)",
)


class _PrometheusOutputHandler:
    """CodeCarbon 3.x output_handler that increments the Prometheus counter.

    CodeCarbon calls handler.out(total, delta) after each measurement cycle.
    'delta.emissions' is the CO2 emitted (kg CO2eq) during that cycle.
    """

    def out(self, total, delta) -> None:  # noqa: ANN001
        delta_mg = (delta.emissions or 0.0) * 1_000_000  # kg → mg
        co2_counter.inc(delta_mg)
        logger.info(
            f"[CodeCarbon] measurement — delta={delta_mg:.6f} mg, "
            f"cumulative={(total.emissions or 0.0) * 1_000_000:.6f} mg CO2eq"
        )


_carbon_tracker = OfflineEmissionsTracker(
    country_iso_code=os.getenv("CODECARBON_COUNTRY_ISO_CODE", "FRA"),
    measure_power_secs=15,
    save_to_file=False,
    log_level="warning",
    force_cpu_power=float(os.getenv("CODECARBON_CPU_POWER_WATTS", "15")),
    output_handlers=[_PrometheusOutputHandler()],
)
try:
    _carbon_tracker.start()
    logger.info("[CodeCarbon] tracker started (measure_power_secs=15, country=FRA)")
    atexit.register(_carbon_tracker.stop)
except Exception as _e:
    logger.warning(f"CodeCarbon tracker could not start: {_e}")
# --- end carbon tracking ---

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
# Check si on devrait mettre le service name lié à k8s
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
