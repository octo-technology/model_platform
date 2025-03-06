from abc import ABC, abstractmethod

from model_platform.domain.entities.role import ProjectRole, Role
from model_platform.domain.entities.user import User


class UserHandler(ABC):

    @abstractmethod
    def get_user(self, email: str, hashed_password: str) -> User:
        pass

    @abstractmethod
    def add_user(self, email: str, hashed_password: str, role: Role) -> bool:
        pass

    @abstractmethod
    def add_project_user(self, project_name: str, email: str, role: ProjectRole) -> bool:
        pass
