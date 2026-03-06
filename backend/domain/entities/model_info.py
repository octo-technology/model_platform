# Philippe Stepniewski
from typing import Optional

from pydantic import BaseModel


class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    project_name: str
    model_card: Optional[str] = None
    risk_level: Optional[str] = None  # e.g. "unacceptable" | "high" | "limited" | "minimal"
    generated_model_card: Optional[str] = None
    act_review: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "project_name": self.project_name,
            "model_card": self.model_card,
            "risk_level": self.risk_level,
            "generated_model_card": self.generated_model_card,
            "act_review": self.act_review,
        }
