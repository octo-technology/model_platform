from abc import ABC, abstractmethod

from model_platform.domain.entities.project import Project


class ProjectDbHandler(ABC):
    @abstractmethod
    def list_projects(self) -> list[Project]:
        pass

    @abstractmethod
    def get_project(self, name) -> Project:
        pass

    @abstractmethod
    def add_project(self, project: Project) -> bool:
        pass

    @abstractmethod
    def remove_project(self, name) -> bool:
        pass
