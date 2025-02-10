from abc import ABC, abstractmethod


class Deployment(ABC):

    @abstractmethod
    def create_deployment(self, project_name: str):
        pass
