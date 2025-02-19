from abc import ABC, abstractmethod

from model_platform.domain.entities.model_deployment import ModelDeployment


class LogModelDeployment(ABC):

    @abstractmethod
    def add_deployment(self, model_deployment: ModelDeployment) -> bool:
        pass

    @abstractmethod
    def remove_deployment(self, model_deployment: ModelDeployment) -> bool:
        pass
