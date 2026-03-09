"""Demo API routes for user behavior simulation and DS simulation.

This module provides endpoints to manage:
- User behavior simulations: periodic calls to a deployed model endpoint
- DS simulations: training and pushing model versions to MLflow
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field


class StartSimulationRequest(BaseModel):
    """Request model for starting a simulation."""

    project_name: str
    model_name: str
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
        The simulation start request with project and model
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


# ── DS Simulation routes ───────────────────────────────────────────────────────


class StartDSSimulationRequest(BaseModel):
    """Request model for starting a DS simulation."""

    project_name: str
    model_name: str
    num_versions: int = Field(default=3, ge=1, le=20)
    interval_seconds: int = Field(default=60, ge=10)


class StopDSSimulationRequest(BaseModel):
    """Request model for stopping a DS simulation."""

    simulation_id: str


class RestartDSSimulationRequest(BaseModel):
    """Request model for restarting a DS simulation."""

    simulation_id: str


def get_ds_simulation_manager(request: Request):
    """Dependency to get the DS simulation manager from app state."""
    return request.app.state.ds_simulation_manager


@router.post("/ds/start")
async def start_ds_simulation(
    req: StartDSSimulationRequest,
    ds_manager=Depends(get_ds_simulation_manager),
) -> dict:
    """Start a Data Scientist simulation for a given project and model.

    Simulates a DS who trains and pushes ``num_versions`` model versions to the
    project's MLflow registry, waiting ``interval_seconds`` between each push.
    Hyperparameters are slightly randomized each iteration to mimic real
    experimentation.

    Parameters
    ----------
    req : StartDSSimulationRequest
        Project name, model name, number of versions, and interval
    ds_manager : DSSimulationManager
        The DS simulation manager from app state

    Returns
    -------
    dict
        Status and simulation details including the simulation_id
    """
    try:
        return await ds_manager.start_simulation(
            project_name=req.project_name,
            model_name=req.model_name,
            num_versions=req.num_versions,
            interval_seconds=req.interval_seconds,
        )
    except Exception as e:
        logger.error(f"Failed to start DS simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start DS simulation")


@router.post("/ds/stop")
async def stop_ds_simulation(
    req: StopDSSimulationRequest,
    ds_manager=Depends(get_ds_simulation_manager),
) -> dict:
    """Interrupt a running DS simulation.

    The current training run completes before the simulation stops.

    Parameters
    ----------
    req : StopDSSimulationRequest
        The simulation_id to stop
    ds_manager : DSSimulationManager
        The DS simulation manager from app state

    Returns
    -------
    dict
        Status and final statistics
    """
    try:
        return await ds_manager.stop_simulation(simulation_id=req.simulation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to stop DS simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop DS simulation")


@router.post("/ds/restart")
async def restart_ds_simulation(
    req: RestartDSSimulationRequest,
    ds_manager=Depends(get_ds_simulation_manager),
) -> dict:
    """Restart a completed DS simulation with the same parameters.

    Parameters
    ----------
    req : RestartDSSimulationRequest
        The simulation_id to restart
    ds_manager : DSSimulationManager
        The DS simulation manager from app state

    Returns
    -------
    dict
        Status and new simulation details
    """
    try:
        return await ds_manager.restart_simulation(simulation_id=req.simulation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restart DS simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart DS simulation")


@router.get("/ds/list")
def list_ds_simulations(
    ds_manager=Depends(get_ds_simulation_manager),
) -> dict:
    """List all DS simulations with their current status.

    Parameters
    ----------
    ds_manager : DSSimulationManager
        The DS simulation manager from app state

    Returns
    -------
    dict
        List of all DS simulations with parameters and runtime statistics
    """
    try:
        result = ds_manager.list_simulations()
        simulations_list = result.get("simulations", []) if isinstance(result, dict) else []
        logger.debug(f"Listing {len(simulations_list)} DS simulations")
        return {"simulations": simulations_list}
    except Exception as e:
        logger.error(f"Failed to list DS simulations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list DS simulations")
