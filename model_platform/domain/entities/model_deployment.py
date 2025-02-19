from pydantic import BaseModel


class ModelDeployment(BaseModel):
    project_name: str
    model_name: str
    version: int
    deployment_name: str
    deployment_date: str

    def to_json(self) -> dict:
        return {
            "project_name": self.project_name,
            "model_name": self.model_name,
            "version": self.version,
            "deployment_name": self.deployment_name,
            "deployment_date": self.deployment_date,
        }
