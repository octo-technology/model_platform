import io
import json
import mlflow.pyfunc
import numpy as np
import tensorflow as tf
from PIL import Image

# TODO à corriger
class MarkerQualityControlWrapper():

    def load_context(self, context):
        pass
        #TODO à compléter

    def predict(self, context, model_input):
        #TODO à compléter
        result = None
        result = result.numpy().tolist()[0]
        return result


mlflow.models.set_model(MarkerQualityControlWrapper())
