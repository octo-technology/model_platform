from abc import ABC, abstractmethod

from backend.domain.entities.agent_info import AgentInfo


class AgentInfoDbHandler(ABC):
    @abstractmethod
    def add_agent_info(self, agent_info: AgentInfo) -> bool:
        pass

    @abstractmethod
    def get_agent_info(self, agent_name: str, agent_version: str, project_name: str) -> AgentInfo:
        pass

    @abstractmethod
    def list_agent_infos_for_project(self, project_name: str) -> list[AgentInfo]:
        pass

    @abstractmethod
    def update_agent_card(self, agent_name: str, agent_version: str, project_name: str, agent_card: str) -> bool:
        pass

    @abstractmethod
    def update_act_review(self, agent_name: str, agent_version: str, project_name: str, text: str) -> bool:
        pass

    @abstractmethod
    def update_risk_level(self, agent_name: str, agent_version: str, project_name: str, risk_level: str) -> bool:
        pass

    @abstractmethod
    def update_suggested_risk_level(
        self, agent_name: str, agent_version: str, project_name: str, suggested_risk_level: str
    ) -> bool:
        pass

    @abstractmethod
    def update_compliance_statuses(
        self,
        agent_name: str,
        agent_version: str,
        project_name: str,
        deterministic_compliance: str | None = None,
        llm_compliance: str | None = None,
    ) -> bool:
        pass

    @abstractmethod
    def delete_agent_info(self, agent_name: str, agent_version: str, project_name: str) -> bool:
        pass

    @abstractmethod
    def search_agent_infos(self, query: str, project_name: str | None = None) -> list[AgentInfo]:
        pass
