import io
import json
import mlflow.pyfunc
import numpy as np
import tensorflow as tf
from PIL import Image


class MarkerQualityControlWrapper(mlflow.pyfunc.PythonModel):

    def load_context(self, context):
        self.model = tf.saved_model.load(context.artifacts["model_path"])

    def predict(self, context, model_input):
        image = Image.open(io.BytesIO(model_input))
        img_array = np.array(image)
        img = tf.convert_to_tensor(img_array, dtype=tf.float32)
        img = tf.expand_dims(img, axis=0)
        img = img / 255.0
        result = self.model(inputs=img)
        result = result.numpy().tolist()[0]
        return result


mlflow.models.set_model(MarkerQualityControlWrapper())
