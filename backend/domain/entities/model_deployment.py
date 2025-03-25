from datetime import datetime

from pydantic import BaseModel


class ModelDeployment(BaseModel):
    project_name: str
    model_name: str
    model_version: str
    deployment_name: str
    deployment_date: int

    def to_json(self) -> dict:
        return {
            "project_name": self.project_name,
            "model_name": self.model_name,
            "version": self.model_version,
            "deployment_name": self.deployment_name,
            "deployment_date": str(datetime.fromtimestamp(self.deployment_date)),
        }
