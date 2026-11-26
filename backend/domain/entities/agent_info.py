from typing import Optional

from pydantic import BaseModel


class AgentTool(BaseModel):
    name: str
    description: Optional[str] = None


class AgentInfo(BaseModel):
    agent_name: str
    agent_version: str
    project_name: str
    description: Optional[str] = None
    agent_type: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    tools: list[AgentTool] = []
    guardrails: Optional[str] = None
    max_iterations: Optional[int] = None
    agent_card: Optional[str] = None
    risk_level: Optional[str] = None  # e.g. "unacceptable" | "high" | "limited" | "minimal"
    deterministic_compliance: Optional[str] = "not_evaluated"
    llm_compliance: Optional[str] = "not_evaluated"
    act_review: Optional[str] = None
    suggested_risk_level: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "project_name": self.project_name,
            "description": self.description,
            "agent_type": self.agent_type,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "tools": [tool.model_dump() for tool in self.tools],
            "guardrails": self.guardrails,
            "max_iterations": self.max_iterations,
            "agent_card": self.agent_card,
            "risk_level": self.risk_level,
            "suggested_risk_level": self.suggested_risk_level,
            "deterministic_compliance": self.deterministic_compliance,
            "llm_compliance": self.llm_compliance,
            "act_review": self.act_review,
        }
