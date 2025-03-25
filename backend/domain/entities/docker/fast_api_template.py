from typing import Any, Dict

import mlflow
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

# model = pickle.load(open("/opt/mlflow/model.pkl", "rb"))
model = mlflow.pyfunc.load_model("/opt/mlflow/")

logger.info("Model loaded successfully")
app = FastAPI(reload=True)


class PredictionRequest(BaseModel):
    inputs: Dict[str, Any]


class PredictionResponse(BaseModel):
    predictions: Any


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        input_data = request.inputs
        logger.info("Received data for inference")
        if isinstance(input_data, dict):
            input_df = pd.DataFrame([input_data])
        else:
            input_df = np.array(input_data)
        # predict
        model_predict = model.predict(pd.DataFrame(input_df))
        logger.info("Model inference done.")
        if isinstance(model_predict, np.ndarray):
            model_predict = model_predict.tolist()
        return PredictionResponse(predictions=model_predict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
