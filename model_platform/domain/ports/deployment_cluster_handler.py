from abc import ABC, abstractmethod


class DeploymentClusterHandler(ABC):

    @abstractmethod
    def get_status(self) -> str:
        pass

    def check_deployment_status(self, deployment_name: str) -> str:
        pass
