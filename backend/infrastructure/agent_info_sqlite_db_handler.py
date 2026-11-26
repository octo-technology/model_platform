import json
import logging
import sqlite3

from backend.domain.entities.agent_info import AgentInfo, AgentTool
from backend.domain.ports.agent_info_db_handler import AgentInfoDbHandler


class AgentInfoDoesntExistError(Exception):
    def __init__(self, message, agent_name=None, agent_version=None, project_name=None):
        super().__init__(message)
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.project_name = project_name


class AgentInfoAlreadyExistError(Exception):
    def __init__(self, message, agent_name=None, agent_version=None, project_name=None):
        super().__init__(message)
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.project_name = project_name


def map_rows_to_agent_infos(rows: list) -> list[AgentInfo]:
    result = []
    for row in rows:
        # columns: 0=id, 1=agent_name, 2=agent_version, 3=project_name,
        #          4=description, 5=agent_type, 6=llm_provider, 7=llm_model,
        #          8=tools (JSON text), 9=guardrails (JSON text), 10=max_iterations,
        #          11=agent_card, 12=risk_level, 13=deterministic_compliance,
        #          14=llm_compliance, 15=act_review, 16=suggested_risk_level
        tools_raw = row[8]
        tools = [AgentTool(**t) for t in json.loads(tools_raw)] if tools_raw else []
        guardrails_raw = row[9]
        guardrails = json.loads(guardrails_raw) if guardrails_raw else None
        result.append(
            AgentInfo(
                agent_name=row[1],
                agent_version=row[2],
                project_name=row[3],
                description=row[4],
                agent_type=row[5],
                llm_provider=row[6],
                llm_model=row[7],
                tools=tools,
                guardrails=guardrails,
                max_iterations=row[10],
                agent_card=row[11],
                risk_level=row[12],
                deterministic_compliance=row[13] if row[13] is not None else "not_evaluated",
                llm_compliance=row[14] if row[14] is not None else "not_evaluated",
                act_review=row[15],
                suggested_risk_level=row[16],
            )
        )
    return result


class AgentInfoSQLiteDBHandler(AgentInfoDbHandler):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table_if_not_exists()

    def _init_table_if_not_exists(self):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_infos (
                    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name                TEXT NOT NULL,
                    agent_version             TEXT NOT NULL,
                    project_name              TEXT NOT NULL,
                    description               TEXT,
                    agent_type                TEXT,
                    llm_provider              TEXT,
                    llm_model                 TEXT,
                    tools                     TEXT NOT NULL DEFAULT '[]',
                    guardrails                TEXT,
                    max_iterations            INTEGER,
                    agent_card                TEXT,
                    risk_level                TEXT,
                    deterministic_compliance  TEXT DEFAULT 'not_evaluated',
                    llm_compliance            TEXT DEFAULT 'not_evaluated',
                    act_review                TEXT,
                    suggested_risk_level      TEXT,
                    UNIQUE (agent_name, agent_version, project_name)
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def add_agent_info(self, agent_info: AgentInfo) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            self.get_agent_info(
                agent_name=agent_info.agent_name,
                agent_version=agent_info.agent_version,
                project_name=agent_info.project_name,
            )
            raise AgentInfoAlreadyExistError(
                agent_name=agent_info.agent_name,
                agent_version=agent_info.agent_version,
                project_name=agent_info.project_name,
                message="AgentInfo with same (agent_name, agent_version, project_name) already exists",
            )
        except AgentInfoDoesntExistError:
            logging.info("AgentInfo not found yet, ok")
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO agent_infos (
                    agent_name, agent_version, project_name, description, agent_type,
                    llm_provider, llm_model, tools, guardrails, max_iterations,
                    agent_card, risk_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_info.agent_name,
                    agent_info.agent_version,
                    agent_info.project_name,
                    agent_info.description,
                    agent_info.agent_type,
                    agent_info.llm_provider,
                    agent_info.llm_model,
                    json.dumps([tool.model_dump() for tool in agent_info.tools]),
                    json.dumps(agent_info.guardrails),
                    agent_info.max_iterations,
                    agent_info.agent_card,
                    agent_info.risk_level,
                ),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def get_agent_info(self, agent_name: str, agent_version: str, project_name: str) -> AgentInfo:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM agent_infos WHERE agent_name = ? AND agent_version = ? AND project_name = ?",
                (agent_name, agent_version, project_name),
            )
            rows = cursor.fetchall()
        finally:
            connection.close()
        if len(rows) == 1:
            return map_rows_to_agent_infos(rows)[0]
        raise AgentInfoDoesntExistError(
            message="AgentInfo doesn't exist",
            agent_name=agent_name,
            agent_version=agent_version,
            project_name=project_name,
        )

    def list_agent_infos_for_project(self, project_name: str) -> list[AgentInfo]:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM agent_infos WHERE project_name = ?", (project_name,))
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_agent_infos(rows)

    def update_agent_card(self, agent_name: str, agent_version: str, project_name: str, agent_card: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET agent_card = ? WHERE agent_name = ? AND agent_version = ? AND project_name = ?",
                (agent_card, agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_act_review(self, agent_name: str, agent_version: str, project_name: str, text: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET act_review = ? WHERE agent_name = ? AND agent_version = ? AND project_name = ?",
                (text, agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_risk_level(self, agent_name: str, agent_version: str, project_name: str, risk_level: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET risk_level = ? WHERE agent_name = ? AND agent_version = ? AND project_name = ?",
                (risk_level, agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_suggested_risk_level(
        self, agent_name: str, agent_version: str, project_name: str, suggested_risk_level: str
    ) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET suggested_risk_level = ?"
                " WHERE agent_name = ? AND agent_version = ? AND project_name = ?",
                (suggested_risk_level, agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_compliance_statuses(
        self,
        agent_name: str,
        agent_version: str,
        project_name: str,
        deterministic_compliance: str | None = None,
        llm_compliance: str | None = None,
    ) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            updates = []
            values = []
            if deterministic_compliance is not None:
                updates.append("deterministic_compliance = ?")
                values.append(deterministic_compliance)
            if llm_compliance is not None:
                updates.append("llm_compliance = ?")
                values.append(llm_compliance)
            if not updates:
                return True
            values.extend([agent_name, agent_version, project_name])
            cursor.execute(
                f"UPDATE agent_infos SET {', '.join(updates)}"
                " WHERE agent_name = ? AND agent_version = ? AND project_name = ?",
                values,
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def delete_agent_info(self, agent_name: str, agent_version: str, project_name: str) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM agent_infos WHERE agent_name = ? AND agent_version = ? AND project_name = ?",
                (agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def search_agent_infos(self, query: str, project_name: str | None = None) -> list[AgentInfo]:
        pattern = f"%{query}%"
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            if project_name:
                cursor.execute(
                    "SELECT * FROM agent_infos WHERE project_name = ?"
                    " AND (agent_card LIKE ? OR description LIKE ? OR agent_type LIKE ? OR risk_level LIKE ?)",
                    (project_name, pattern, pattern, pattern, pattern),
                )
            else:
                cursor.execute(
                    "SELECT * FROM agent_infos"
                    " WHERE agent_card LIKE ? OR description LIKE ? OR agent_type LIKE ? OR risk_level LIKE ?",
                    (pattern, pattern, pattern, pattern),
                )
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_agent_infos(rows)
