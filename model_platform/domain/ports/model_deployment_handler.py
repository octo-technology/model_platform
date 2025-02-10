from abc import ABC, abstractmethod


class ModelDeployment(ABC):

    @abstractmethod
    def create_model_deployment(self, project_name: str, model_name: str, version: str):
        pass
