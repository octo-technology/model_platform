import mlflow
from model_platform.ports.model_registry import ModelRegistry

class MLflowAdapter(ModelRegistry):
    def __init__(self, mlflow_url):
        self.mlflow_url = mlflow_url

    def list_models(self, project):
        mlflow.set_tracking_uri(project.mlflow_url)
        return mlflow.search_registered_models()
