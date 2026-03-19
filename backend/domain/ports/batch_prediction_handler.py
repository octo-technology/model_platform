# Philippe Stepniewski
from abc import ABC, abstractmethod

from backend.domain.entities.batch_prediction import BatchPrediction


class BatchPredictionHandler(ABC):
    @abstractmethod
    def create_batch_job(
        self, project_name: str, model_name: str, model_version: str, input_path: str, output_path: str, job_id: str
    ) -> BatchPrediction:
        pass

    @abstractmethod
    def get_job_status(self, project_name: str, job_id: str) -> BatchPrediction:
        pass

    @abstractmethod
    def list_batch_jobs(self, project_name: str) -> list[BatchPrediction]:
        pass

    @abstractmethod
    def delete_batch_job(self, project_name: str, job_id: str) -> bool:
        pass

    @abstractmethod
    def list_finished_jobs(self, project_name: str) -> list[BatchPrediction]:
        pass
