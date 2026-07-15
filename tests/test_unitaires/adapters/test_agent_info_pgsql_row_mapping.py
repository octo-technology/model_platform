from backend.infrastructure.agent_info_pgsql_db_handler import _map_pgsql_rows_to_agent_infos


def _row(tools=None, guardrails=None):
    # Mirrors the `agent_infos` table column order (see agent_info_pgsql_db_handler.py).
    return (
        1,  # id
        "my_agent",  # agent_name
        "1",  # agent_version
        "my_project",  # project_name
        "desc",  # description
        "react",  # agent_type
        "mammouth",  # llm_provider
        "gpt-4.1",  # llm_model
        tools if tools is not None else [],  # tools — psycopg2 decodes JSONB to a Python list
        guardrails,  # guardrails — psycopg2 decodes JSONB to a Python str/None
        2,  # max_iterations
        "card",  # agent_card
        "limited",  # risk_level
        None,  # deterministic_compliance
        None,  # llm_compliance
        None,  # act_review
        None,  # suggested_risk_level
    )


class TestMapPgsqlRowsToAgentInfos:
    def test_tools_already_decoded_by_psycopg2_as_list_of_dicts(self):
        row = _row(tools=[{"name": "get_schema", "description": "Returns the DB schema"}])

        agents = _map_pgsql_rows_to_agent_infos([row])

        assert len(agents) == 1
        assert agents[0].tools[0].name == "get_schema"
        assert agents[0].tools[0].description == "Returns the DB schema"

    def test_empty_tools_list(self):
        agents = _map_pgsql_rows_to_agent_infos([_row(tools=[])])

        assert agents[0].tools == []

    def test_guardrails_already_decoded_by_psycopg2_as_plain_string(self):
        row = _row(guardrails='{"sql_read_only": "SELECT/WITH only"}')

        agents = _map_pgsql_rows_to_agent_infos([row])

        assert agents[0].guardrails == '{"sql_read_only": "SELECT/WITH only"}'

    def test_guardrails_none(self):
        agents = _map_pgsql_rows_to_agent_infos([_row(guardrails=None)])

        assert agents[0].guardrails is None
