import json
import logging

import psycopg2

from backend.domain.entities.agent_info import AgentInfo, AgentTool
from backend.domain.ports.agent_info_db_handler import AgentInfoDbHandler
from backend.infrastructure.agent_info_sqlite_db_handler import (
    AgentInfoAlreadyExistError,
    AgentInfoDoesntExistError,
)


def _map_pgsql_rows_to_agent_infos(rows: list) -> list[AgentInfo]:
    """psycopg2 auto-decodes JSONB columns (tools, guardrails) into native Python
    objects, unlike the sqlite handler's TEXT columns which hold JSON-encoded
    strings and need an explicit json.loads (see map_rows_to_agent_infos)."""
    result = []
    for row in rows:
        tools_raw = row[8] or []
        tools = [AgentTool(**t) if isinstance(t, dict) else AgentTool(name=str(t)) for t in tools_raw]
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
                guardrails=row[9],
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


class AgentInfoPostgresDBHandler(AgentInfoDbHandler):
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.db_config["dbname"] = "model_platform_db"
        self._init_table_if_not_exists()

    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def _init_table_if_not_exists(self):
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_infos (
                    id                        SERIAL PRIMARY KEY,
                    agent_name                TEXT NOT NULL,
                    agent_version             TEXT NOT NULL,
                    project_name              TEXT NOT NULL,
                    description               TEXT,
                    agent_type                TEXT,
                    llm_provider              TEXT,
                    llm_model                 TEXT,
                    tools                     JSONB NOT NULL DEFAULT '[]',
                    guardrails                JSONB,
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
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_infos_fts
                ON agent_infos USING GIN (
                    to_tsvector('simple',
                        COALESCE(agent_card, '') || ' ' ||
                        COALESCE(description, '') || ' ' ||
                        COALESCE(agent_type, '') || ' ' ||
                        COALESCE(risk_level, '')
                    )
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def add_agent_info(self, agent_info: AgentInfo) -> bool:
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
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO agent_infos (
                    agent_name, agent_version, project_name, description, agent_type,
                    llm_provider, llm_model, tools, guardrails, max_iterations,
                    agent_card, risk_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM agent_infos WHERE agent_name = %s AND agent_version = %s AND project_name = %s",
                (agent_name, agent_version, project_name),
            )
            rows = cursor.fetchall()
        finally:
            connection.close()
        if len(rows) == 1:
            return _map_pgsql_rows_to_agent_infos(rows)[0]
        raise AgentInfoDoesntExistError(
            message="AgentInfo doesn't exist",
            agent_name=agent_name,
            agent_version=agent_version,
            project_name=project_name,
        )

    def list_agent_infos_for_project(self, project_name: str) -> list[AgentInfo]:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM agent_infos WHERE project_name = %s", (project_name,))
            rows = cursor.fetchall()
        finally:
            connection.close()
        return _map_pgsql_rows_to_agent_infos(rows)

    def update_agent_card(self, agent_name: str, agent_version: str, project_name: str, agent_card: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET agent_card = %s"
                " WHERE agent_name = %s AND agent_version = %s AND project_name = %s",
                (agent_card, agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_act_review(self, agent_name: str, agent_version: str, project_name: str, text: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET act_review = %s"
                " WHERE agent_name = %s AND agent_version = %s AND project_name = %s",
                (text, agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_risk_level(self, agent_name: str, agent_version: str, project_name: str, risk_level: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET risk_level = %s"
                " WHERE agent_name = %s AND agent_version = %s AND project_name = %s",
                (risk_level, agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def update_suggested_risk_level(
        self, agent_name: str, agent_version: str, project_name: str, suggested_risk_level: str
    ) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE agent_infos SET suggested_risk_level = %s"
                " WHERE agent_name = %s AND agent_version = %s AND project_name = %s",
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
        connection = self._connect()
        try:
            cursor = connection.cursor()
            updates = []
            values = []
            if deterministic_compliance is not None:
                updates.append("deterministic_compliance = %s")
                values.append(deterministic_compliance)
            if llm_compliance is not None:
                updates.append("llm_compliance = %s")
                values.append(llm_compliance)
            if not updates:
                return True
            values.extend([agent_name, agent_version, project_name])
            cursor.execute(
                f"UPDATE agent_infos SET {', '.join(updates)}"
                " WHERE agent_name = %s AND agent_version = %s AND project_name = %s",
                values,
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def delete_agent_info(self, agent_name: str, agent_version: str, project_name: str) -> bool:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM agent_infos WHERE agent_name = %s AND agent_version = %s AND project_name = %s",
                (agent_name, agent_version, project_name),
            )
            connection.commit()
        finally:
            connection.close()
            return True

    def search_agent_infos(self, query: str, project_name: str | None = None) -> list[AgentInfo]:
        fts_condition = (
            "to_tsvector('simple',"
            " COALESCE(agent_card, '') || ' ' ||"
            " COALESCE(description, '') || ' ' ||"
            " COALESCE(agent_type, '') || ' ' ||"
            " COALESCE(risk_level, '')"
            ") @@ websearch_to_tsquery('simple', %s)"
        )
        connection = self._connect()
        try:
            cursor = connection.cursor()
            if project_name:
                cursor.execute(
                    f"SELECT * FROM agent_infos WHERE project_name = %s AND ({fts_condition})",
                    (project_name, query),
                )
            else:
                cursor.execute(
                    f"SELECT * FROM agent_infos WHERE {fts_condition}",
                    (query,),
                )
            rows = cursor.fetchall()
        finally:
            connection.close()
        return _map_pgsql_rows_to_agent_infos(rows)
