from abc import ABC, abstractmethod

from model_platform.domain.entities.role import Role
from model_platform.domain.entities.user import User


class UserHandler(ABC):

    @abstractmethod
    def get_user(self, email: str, hashed_password: str) -> User:
        pass

    @abstractmethod
    def add_user(self, email: str, hashed_password: str, role: Role) -> bool:
        pass
