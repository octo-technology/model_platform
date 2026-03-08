"""Demo API routes for user behavior simulation.

This module provides endpoints to manage user behavior simulations
on deployed models, allowing testing and monitoring of model performance.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field


class StartSimulationRequest(BaseModel):
    """Request model for starting a simulation."""
    project_name: str
    model_name: str
    model_version: str
    duration_minutes: int = Field(default=5, ge=1, le=30)  # 1 to 30 minutes max
    num_users: int = Field(default=1, ge=1)  # At least 1 user


class StopSimulationRequest(BaseModel):
    """Request model for stopping a simulation."""
    simulation_id: str


class RestartSimulationRequest(BaseModel):
    """Request model for restarting a simulation."""
    simulation_id: str


router = APIRouter()


def get_simulation_manager(request: Request):
    """Dependency to get the simulation manager from app state."""
    return request.app.state.simulation_manager


@router.post("/start")
async def start_simulation(
    req: StartSimulationRequest,
    simulation_manager=Depends(get_simulation_manager),
) -> dict:
    """Start a user behavior simulation for a deployed model.

    This endpoint starts a background simulation that periodically invokes
    a deployed model endpoint with randomly generated data.

    Parameters
    ----------
    req : StartSimulationRequest
        The simulation start request with project, model, and version
    simulation_manager : SimulationManager
        The simulation manager from app state

    Returns
    -------
    dict
        Status information about the started simulation
    """
    try:
        return await simulation_manager.start_simulation(
            project_name=req.project_name,
            model_name=req.model_name,
            model_version=req.model_version,
            duration_minutes=req.duration_minutes,
            num_users=req.num_users,
        )
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start simulation")


@router.post("/stop")
async def stop_simulation(
    req: StopSimulationRequest,
    simulation_manager=Depends(get_simulation_manager),
) -> dict:
    """Stop a running user behavior simulation.

    Parameters
    ----------
    req : StopSimulationRequest
        The simulation stop request with simulation_id
    simulation_manager : SimulationManager
        The simulation manager from app state

    Returns
    -------
    dict
        Status information about the stopped simulation
    """
    try:
        return await simulation_manager.stop_simulation(simulation_id=req.simulation_id)
    except Exception as e:
        logger.error(f"Failed to stop simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop simulation")


@router.post("/restart")
async def restart_simulation(
    req: RestartSimulationRequest,
    simulation_manager=Depends(get_simulation_manager),
) -> dict:
    """Restart a terminated user behavior simulation.

    This endpoint restarts a stopped simulation with the same parameters
    as the original simulation.

    Parameters
    ----------
    req : RestartSimulationRequest
        The simulation restart request with simulation_id
    simulation_manager : SimulationManager
        The simulation manager from app state

    Returns
    -------
    dict
        Status information about the restarted simulation
    """
    try:
        return await simulation_manager.restart_simulation(simulation_id=req.simulation_id)
    except Exception as e:
        logger.error(f"Failed to restart simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart simulation")


@router.get("/list")
def list_all_simulations(
    simulation_manager=Depends(get_simulation_manager),
) -> dict:
    """List all active simulations.

    Parameters
    ----------
    simulation_manager : SimulationManager
        The simulation manager from app state

    Returns
    -------
    dict
        List of all simulations with their status
    """
    try:
        result = simulation_manager.list_simulations()
        simulations_list = result.get("simulations", []) if isinstance(result, dict) else []
        logger.debug(f"Listing {len(simulations_list)} simulations")
        return {"simulations": simulations_list}
    except Exception as e:
        logger.error(f"Failed to list simulations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list simulations")
