# Philippe Stepniewski
from abc import ABC, abstractmethod


class PlatformConfigHandler(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass
