import typer

from cli.utils.api_calls import get_and_print


def list_agents(project_name: str):
    """List existing agents for a project"""
    get_and_print(
        f"/{project_name}/agents/list", "❌ Error retrieving agents", success_message="✅ Agents retrieved successfully"
    )


def deploy_agent(project_name: str, agent_name: str = typer.Option(), agent_version: str = typer.Option()):
    """Deploy a new agent to a project"""
    get_and_print(
        f"/{project_name}/agents/deploy/{agent_name}/{agent_version}",
        "❌ Error deploying agent",
        success_message="✅ Agent deployed successfully",
    )


def undeploy_agent(project_name: str, agent_name: str = typer.Option(), agent_version: str = typer.Option()):
    """Undeploy an agent from a project"""
    get_and_print(
        f"/{project_name}/agents/undeploy/{agent_name}/{agent_version}",
        "❌ Error undeploying agent",
        success_message="✅ Agent undeployed successfully",
    )


def list_deployed_agents(project_name: str):
    """List deployed agents for a project"""
    get_and_print(
        f"/{project_name}/deployed_agents/list",
        "❌ Error retrieving deployed agents",
        success_message="✅ Deployed agents retrieved successfully",
    )


def get_agent_info(project_name: str, agent_name: str = typer.Option(), agent_version: str = typer.Option()):
    """Show compliance metadata (tools, guardrails, agent card, risk level) for one agent version"""
    get_and_print(
        f"/agent_infos/{project_name}/{agent_name}/{agent_version}",
        "❌ Error retrieving agent info",
        success_message="✅ Agent info retrieved successfully",
    )


def search_agent_infos(query: str = typer.Option(), project_name: str | None = typer.Option(default=None)):
    """Search agent infos by text query. Scope to a project with --project-name, or search the whole platform."""
    endpoint = f"/agent_infos/search?query={query}"
    if project_name is not None:
        endpoint += f"&project_name={project_name}"
    get_and_print(endpoint, "❌ Error searching agent infos")
