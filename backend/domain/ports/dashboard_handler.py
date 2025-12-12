from abc import ABC, abstractmethod


class DashboardHandler(ABC):

    @abstractmethod
    def generate_dashboard_uid(self, project_name: str, model_name: str, version: str) -> str:
        """Generate a unique dashboard UID for the given model.

        Each implementation should generate a UID that respects its own constraints
        (e.g., Grafana has a 40 character limit).

        Args:
            project_name: The name of the project.
            model_name: The name of the model.
            version: The version of the model.

        Returns:
            A unique dashboard UID string.
        """
        pass

    @abstractmethod
    def create_dashboard(
        self, project_name: str, model_name: str, version: str, service_name: str, dashboard_uid: str
    ) -> bool:
        pass

    @abstractmethod
    def delete_dashboard(self, project_name: str, model_name: str, version: str, dashboard_uid: str) -> bool:
        pass
