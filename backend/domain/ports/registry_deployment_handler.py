from abc import ABC, abstractmethod


class RegistryDeployment(ABC):

    @abstractmethod
    def create_registry_deployment(self):
        pass
