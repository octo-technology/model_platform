from typing import Any, Dict, Optional

import mlflow
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from loguru import logger
from pydantic import BaseModel

try:
    logger.info("Starting up and loading model...")
    model = mlflow.pyfunc.load_model("/opt/mlflow/")
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
app = FastAPI(reload=True)


class PredictionRequest(BaseModel):
    inputs: Dict[str, Any]


class PredictionResponse(BaseModel):
    outputs: Any


@app.post("/predict", response_model=PredictionResponse)
async def predict(
        request: Request,
        file: Optional[UploadFile] = File(None)
):
    try:
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            if not file:
                raise HTTPException(status_code=400, detail="No file uploaded")
            contents = await file.read()
            logger.info("Received file for inference")
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
