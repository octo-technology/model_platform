# Philippe Stepniewski
from abc import ABC, abstractmethod

from backend.domain.entities.model_info import ModelInfo


class ModelInfoDbHandler(ABC):
    @abstractmethod
    def add_model_info(self, model_info: ModelInfo) -> bool:
        pass

    @abstractmethod
    def get_model_info(self, model_name: str, model_version: str, project_name: str) -> ModelInfo:
        pass

    @abstractmethod
    def list_model_infos_for_project(self, project_name: str) -> list[ModelInfo]:
        pass

    @abstractmethod
    def update_model_card(self, model_name: str, model_version: str, project_name: str, model_card: str) -> bool:
        pass

    @abstractmethod
    def delete_model_info(self, model_name: str, model_version: str, project_name: str) -> bool:
        pass

    @abstractmethod
    def search_model_infos(self, query: str, project_name: str | None = None) -> list[ModelInfo]:
        pass
