import typer
from pydantic import BaseModel, Field

from cli.utils.api_calls import get_and_print, post_and_print


class StartSimulationRequest(BaseModel):
    """Request model for starting a simulation."""
    project_name: str
    model_name: str
    model_version: str
    duration_minutes: int = Field(default=5, ge=1, le=10)
    num_users: int = Field(default=1, ge=1)


class StopSimulationRequest(BaseModel):
    """Request model for stopping a simulation."""
    project_name: str
    model_name: str
    model_version: str


def list_simulations():
    """List all active simulations"""
    get_and_print("/demo/list", "❌ Error fetching simulations")


def start_simulation(
    project_name: str = typer.Option(),
    model_name: str = typer.Option(),
    model_version: str = typer.Option(),
    duration_minutes: int = typer.Option(5, help="Duration in minutes (1-10, default: 5)"),
    num_users: int = typer.Option(1, help="Number of concurrent users per round (default: 1)")
):
    """Start a new simulation for a specific model

    Makes k concurrent endpoint calls per round with random intervals (0.1-5s).
    """
    req = StartSimulationRequest(
        project_name=project_name,
        model_name=model_name,
        model_version=model_version,
        duration_minutes=duration_minutes,
        num_users=num_users
    )
    post_and_print("/demo/start", req.model_dump(), "❌ Error starting simulation", "✅ Simulation started")


def stop_simulation(project_name: str = typer.Option(), model_name: str = typer.Option(), model_version: str = typer.Option()):
    """Stop an active simulation"""
    req = StopSimulationRequest(
        project_name=project_name,
        model_name=model_name,
        model_version=model_version
    )
    post_and_print("/demo/stop", req.model_dump(), "❌ Error stopping simulation", "✅ Simulation stopped")


def get_status(project_name: str = typer.Option(), model_name: str = typer.Option(), model_version: str = typer.Option()):
    """Get the status of a simulation"""
    params = {"project_name": project_name, "model_name": model_name, "model_version": model_version}
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    get_and_print(f"/demo/status?{query_string}", "❌ Error fetching simulation status")
