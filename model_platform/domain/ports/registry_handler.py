from abc import ABC, abstractmethod

from model_platform.domain.ports.model_registry import ModelRegistry


class RegistryHandler(ABC):

    @abstractmethod
    def connect(self, connexion_parameters: dict[str:str]) -> ModelRegistry:
        pass
