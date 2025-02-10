from abc import ABC, abstractmethod


class RegistryDeployment(ABC):

    @abstractmethod
    def create_registry_deployment(self, project_name: str):
        pass
