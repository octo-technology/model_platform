from abc import ABC, abstractmethod


class ModelDeployment(ABC):

    @abstractmethod
    def create_model_deployment(self):
        pass
