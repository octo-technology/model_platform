# Philippe Stepniewski
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class BatchPredictionStatus(str, Enum):
    BUILDING = "building"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchPrediction(BaseModel):
    job_id: str
    project_name: str
    model_name: str
    model_version: str
    status: BatchPredictionStatus
    input_path: str
    output_path: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    row_count: Optional[int] = None

    def to_json(self) -> dict:
        return {
            "job_id": self.job_id,
            "project_name": self.project_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "status": self.status.value,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "row_count": self.row_count,
        }
