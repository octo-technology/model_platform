from abc import ABC, abstractmethod

from model_platform.domain.ports.model_registry import ModelRegistry


class RegistryHandler(ABC):

    @abstractmethod
    def get_registry_adapter(self, project_name: str, tracking_uri: str) -> ModelRegistry:
        pass
