import pickle
from typing import Any, Dict

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

model = pickle.load(open("/opt/mlflow/python_model.pkl", "rb"))
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
        input_df = pd.DataFrame([input_data])
        model_predict = model.predict(model_input=pd.DataFrame(input_df), context=None)
        logger.info("Model inference done.")
        if isinstance(model_predict, np.ndarray):
            model_predict = model_predict.tolist()
        return PredictionResponse(predictions=model_predict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
