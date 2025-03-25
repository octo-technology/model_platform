from abc import ABC, abstractmethod

from backend.domain.entities.role import ProjectRole, Role
from backend.domain.entities.user import User


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

    @abstractmethod
    def get_all_users(self) -> list[str]:
        pass

    @abstractmethod
    def get_users_for_project(self) -> list[dict]:
        pass
