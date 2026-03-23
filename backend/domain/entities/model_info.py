# Philippe Stepniewski
from typing import Optional

from pydantic import BaseModel


class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    project_name: str
    model_card: Optional[str] = None
    risk_level: Optional[str] = None  # e.g. "unacceptable" | "high" | "limited" | "minimal"
    act_review: Optional[str] = None
    suggested_risk_level: Optional[str] = None
    deterministic_compliance: Optional[str] = "not_evaluated"
    llm_compliance: Optional[str] = "not_evaluated"

    def to_json(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "project_name": self.project_name,
            "model_card": self.model_card,
            "risk_level": self.risk_level,
            "suggested_risk_level": self.suggested_risk_level,
            "act_review": self.act_review,
            "deterministic_compliance": self.deterministic_compliance,
            "llm_compliance": self.llm_compliance,
        }
