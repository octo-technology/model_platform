import pytest

from backend.domain.entities.agent_info import AgentInfo, AgentTool
from backend.infrastructure.agent_info_sqlite_db_handler import (
    AgentInfoAlreadyExistError,
    AgentInfoDoesntExistError,
    AgentInfoSQLiteDBHandler,
)


@pytest.fixture
def handler(tmp_path):
    return AgentInfoSQLiteDBHandler(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def basic_agent():
    return AgentInfo(agent_name="my_agent", agent_version="1", project_name="proj_a", risk_level="high")


@pytest.fixture
def agent_with_tools():
    return AgentInfo(
        agent_name="tool_agent",
        agent_version="1",
        project_name="proj_a",
        tools=[AgentTool(name="web_search", description="Search the web"), AgentTool(name="calculator")],
        guardrails="no harmful content",
        max_iterations=10,
    )


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


def test_add_agent_info(handler, basic_agent):
    assert handler.add_agent_info(basic_agent) is True


def test_add_agent_info_duplicate_raises(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    with pytest.raises(AgentInfoAlreadyExistError):
        handler.add_agent_info(basic_agent)


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_agent_info(handler):
    agent = AgentInfo(
        agent_name="my_agent",
        agent_version="1",
        project_name="proj_a",
        agent_card="# Card",
        risk_level="minimal",
        description="A helpful agent",
        agent_type="rag",
        llm_provider="anthropic",
        llm_model="claude-sonnet-4-6",
    )
    handler.add_agent_info(agent)
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.agent_name == "my_agent"
    assert retrieved.agent_version == "1"
    assert retrieved.project_name == "proj_a"
    assert retrieved.agent_card == "# Card"
    assert retrieved.risk_level == "minimal"
    assert retrieved.description == "A helpful agent"
    assert retrieved.agent_type == "rag"
    assert retrieved.llm_provider == "anthropic"
    assert retrieved.llm_model == "claude-sonnet-4-6"


def test_get_agent_info_not_found_raises(handler):
    with pytest.raises(AgentInfoDoesntExistError):
        handler.get_agent_info(agent_name="unknown", agent_version="1", project_name="proj_a")


# ---------------------------------------------------------------------------
# tools and guardrails (JSONB columns)
# ---------------------------------------------------------------------------


def test_add_and_get_agent_with_tools(handler, agent_with_tools):
    handler.add_agent_info(agent_with_tools)
    retrieved = handler.get_agent_info(agent_name="tool_agent", agent_version="1", project_name="proj_a")
    assert len(retrieved.tools) == 2
    tool_names = {t.name for t in retrieved.tools}
    assert tool_names == {"web_search", "calculator"}
    assert retrieved.tools[0].description == "Search the web" or retrieved.tools[1].description == "Search the web"


def test_tools_default_empty_list(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.tools == []


def test_guardrails_persisted(handler, agent_with_tools):
    handler.add_agent_info(agent_with_tools)
    retrieved = handler.get_agent_info(agent_name="tool_agent", agent_version="1", project_name="proj_a")
    assert retrieved.guardrails == "no harmful content"


def test_max_iterations_persisted(handler, agent_with_tools):
    handler.add_agent_info(agent_with_tools)
    retrieved = handler.get_agent_info(agent_name="tool_agent", agent_version="1", project_name="proj_a")
    assert retrieved.max_iterations == 10


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_agent_infos_for_project(handler):
    handler.add_agent_info(AgentInfo(agent_name="agent_a", agent_version="1", project_name="proj_x"))
    handler.add_agent_info(AgentInfo(agent_name="agent_b", agent_version="2", project_name="proj_x"))
    handler.add_agent_info(AgentInfo(agent_name="agent_c", agent_version="1", project_name="proj_y"))
    results = handler.list_agent_infos_for_project(project_name="proj_x")
    assert len(results) == 2
    assert {a.agent_name for a in results} == {"agent_a", "agent_b"}


def test_list_agent_infos_empty_project(handler):
    assert handler.list_agent_infos_for_project(project_name="nonexistent") == []


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update_agent_card(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    handler.update_agent_card(agent_name="my_agent", agent_version="1", project_name="proj_a", agent_card="# Updated")
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.agent_card == "# Updated"
    assert retrieved.risk_level == "high"


def test_update_act_review(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    handler.update_act_review(agent_name="my_agent", agent_version="1", project_name="proj_a", text="Reviewed OK")
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.act_review == "Reviewed OK"


def test_update_risk_level(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    handler.update_risk_level(agent_name="my_agent", agent_version="1", project_name="proj_a", risk_level="minimal")
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.risk_level == "minimal"


def test_update_suggested_risk_level(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    handler.update_suggested_risk_level(
        agent_name="my_agent", agent_version="1", project_name="proj_a", suggested_risk_level="limited"
    )
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.suggested_risk_level == "limited"
    assert retrieved.risk_level == "high"


def test_update_compliance_statuses_both(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    handler.update_compliance_statuses(
        agent_name="my_agent",
        agent_version="1",
        project_name="proj_a",
        deterministic_compliance="compliant",
        llm_compliance="non_compliant",
    )
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.deterministic_compliance == "compliant"
    assert retrieved.llm_compliance == "non_compliant"


def test_update_compliance_statuses_partial(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    handler.update_compliance_statuses(
        agent_name="my_agent", agent_version="1", project_name="proj_a", llm_compliance="compliant"
    )
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.llm_compliance == "compliant"
    assert retrieved.deterministic_compliance == "not_evaluated"


def test_update_compliance_statuses_no_op(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    result = handler.update_compliance_statuses(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert result is True


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_agent_info(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    handler.delete_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    with pytest.raises(AgentInfoDoesntExistError):
        handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


def test_search_by_agent_card(handler):
    handler.add_agent_info(
        AgentInfo(agent_name="agent_a", agent_version="1", project_name="proj_x", agent_card="customer support bot")
    )
    handler.add_agent_info(
        AgentInfo(agent_name="agent_b", agent_version="1", project_name="proj_x", agent_card="data analysis pipeline")
    )
    results = handler.search_agent_infos(query="customer")
    assert len(results) == 1
    assert results[0].agent_name == "agent_a"


def test_search_by_description(handler):
    handler.add_agent_info(
        AgentInfo(agent_name="agent_a", agent_version="1", project_name="proj_x", description="answers FAQ questions")
    )
    handler.add_agent_info(
        AgentInfo(agent_name="agent_b", agent_version="1", project_name="proj_x", description="generates reports")
    )
    results = handler.search_agent_infos(query="FAQ")
    assert len(results) == 1
    assert results[0].agent_name == "agent_a"


def test_search_by_agent_type(handler):
    handler.add_agent_info(AgentInfo(agent_name="agent_a", agent_version="1", project_name="proj_x", agent_type="rag"))
    handler.add_agent_info(
        AgentInfo(agent_name="agent_b", agent_version="1", project_name="proj_x", agent_type="react")
    )
    results = handler.search_agent_infos(query="rag")
    assert len(results) == 1
    assert results[0].agent_name == "agent_a"


def test_search_by_risk_level(handler):
    handler.add_agent_info(AgentInfo(agent_name="agent_a", agent_version="1", project_name="proj_x", risk_level="high"))
    handler.add_agent_info(
        AgentInfo(agent_name="agent_b", agent_version="1", project_name="proj_x", risk_level="minimal")
    )
    results = handler.search_agent_infos(query="high")
    assert len(results) == 1
    assert results[0].agent_name == "agent_a"


def test_search_scoped_to_project(handler):
    handler.add_agent_info(
        AgentInfo(agent_name="agent_a", agent_version="1", project_name="proj_x", description="deep learning agent")
    )
    handler.add_agent_info(
        AgentInfo(agent_name="agent_b", agent_version="1", project_name="proj_y", description="deep learning agent")
    )
    results = handler.search_agent_infos(query="deep", project_name="proj_x")
    assert len(results) == 1
    assert results[0].project_name == "proj_x"


def test_search_no_results(handler):
    handler.add_agent_info(
        AgentInfo(agent_name="agent_a", agent_version="1", project_name="proj_x", agent_card="customer support")
    )
    assert handler.search_agent_infos(query="nonexistent_xyz") == []


# ---------------------------------------------------------------------------
# compliance defaults
# ---------------------------------------------------------------------------


def test_compliance_defaults_on_create(handler, basic_agent):
    handler.add_agent_info(basic_agent)
    retrieved = handler.get_agent_info(agent_name="my_agent", agent_version="1", project_name="proj_a")
    assert retrieved.deterministic_compliance == "not_evaluated"
    assert retrieved.llm_compliance == "not_evaluated"
