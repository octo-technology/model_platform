# Philippe Stepniewski
from abc import ABC, abstractmethod


class ObjectStorageHandler(ABC):
    @abstractmethod
    def ensure_project_space(self, project_name: str) -> None:
        pass

    @abstractmethod
    def remove_project_space(self, project_name: str) -> None:
        pass

    @abstractmethod
    def upload_file(self, project_name: str, remote_path: str, file_content: bytes) -> None:
        pass

    @abstractmethod
    def download_file(self, project_name: str, remote_path: str) -> bytes:
        pass

    @abstractmethod
    def list_files(self, project_name: str, prefix: str = "") -> list[str]:
        pass

    @abstractmethod
    def delete_file(self, project_name: str, remote_path: str) -> None:
        pass

    @abstractmethod
    def file_exists(self, project_name: str, remote_path: str) -> bool:
        pass
