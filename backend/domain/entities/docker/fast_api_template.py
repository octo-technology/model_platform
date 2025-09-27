from typing import Any, Dict

import mlflow
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, File, UploadFile
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
async def predict(request: PredictionRequest = None, file: UploadFile = File(None)):
    try:
        if file:
            contents = await file.read()
            logger.info("Received file for inference")
            model_predict = model.predict(contents)
        elif request:
            input_data = request.inputs
            logger.info("Received JSON data for inference")
            if isinstance(input_data, dict):
                input_df = pd.DataFrame([input_data])
            else:
                input_df = np.array(input_data)
            model_predict = model.predict(pd.DataFrame(input_df))
        else:
            raise HTTPException(status_code=400, detail="No input data provided")
        if isinstance(model_predict, np.ndarray):
            model_predict = model_predict.tolist()
        return PredictionResponse(outputs=model_predict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
