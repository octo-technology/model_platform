"""Use cases for user behavior simulation and demo endpoints.

This module implements the business logic for simulating user behavior
by making periodic calls to deployed model endpoints.
"""

import asyncio
import random
import time
import uuid
from typing import TypedDict

import requests
from loguru import logger

from backend.domain.entities.model_deployment import ModelDeployment
from backend.domain.use_cases.payload_generator import PayloadGenerator, build_feature_specs
from backend.infrastructure.k8s_deployment_cluster_adapter import K8SDeploymentClusterAdapter
from backend.utils import sanitize_project_name


class SimulationStats(TypedDict):
    """Statistics dictionary for simulation tracking."""

    simulation_id: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_call_time: float | None
    last_error: str | None


class UserBehaviorSimulator:
    """Simulates user behavior by making periodic calls to deployed model endpoints."""

    def __init__(
        self,
        project_name: str,
        model_name: str,
        duration_minutes: int = 5,
        num_users: int = 1,
        success_rate: int = 100,
    ):
        """Initialize the simulator.

        Parameters
        ----------
        project_name : str
            The name of the project containing the model
        model_name : str
            The name of the model to target
        duration_minutes : int
            Duration of simulation in minutes (1-10, max 10 minutes)
        num_users : int
            Number of concurrent users making parallel requests per round
        success_rate : int
            Percentage of calls (0-100) that should use a valid payload.
            The remaining calls send a malformed payload to trigger a 4xx/5xx.

        Raises
        ------
        ValueError
            If the model deployment is not found in the project
        """
        self.simulation_id = str(uuid.uuid4())
        self.project_name = project_name
        self.model_name = model_name
        self.duration_minutes = min(duration_minutes, 30)  # Max 30 minutes
        self.num_users = max(1, num_users)
        self.success_rate = max(0, min(100, success_rate))
        self.is_running = False
        self.tasks: list = []
        self.stop_event = asyncio.Event()
        self.statistics: SimulationStats = {
            "simulation_id": self.simulation_id,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_call_time": None,
            "last_error": None,
        }

        # Discover the endpoint URL from K8s deployment
        k8s_adapter = K8SDeploymentClusterAdapter()
        deployed_models: list[ModelDeployment] = k8s_adapter.list_deployments_for_project(project_name)

        deployment = None
        for model in deployed_models:
            if model.model_name == model_name:
                deployment = model
                break

        if not deployment:
            raise ValueError(
                f"Model {model_name} not found in K8s for project {project_name}. "
                f"Please deploy the model first before starting a simulation."
            )

        # Construct the endpoint URL following the pattern:
        # http://service-name.namespace.svc.cluster.local:port/predict
        namespace = sanitize_project_name(project_name)
        self.endpoint_url: str = f"http://{deployment.deployment_name}.{namespace}.svc.cluster.local:8000/predict"
        logger.info(f"Model endpoint discovered: {self.endpoint_url}")

        # Initialize payload generator with dynamically discovered feature specs
        self._payload_generator = PayloadGenerator()
        tracking_uri = f"http://{namespace}.{namespace}.svc.cluster.local:5000"
        logger.info(
            f"Discovering feature specs for {model_name} v{deployment.model_version} from MLflow at {tracking_uri}"
        )
        self._feature_specs = build_feature_specs(tracking_uri, model_name, deployment.model_version)
        if not self._feature_specs:
            logger.warning(f"Falling back to hardcoded credit scoring payload for {model_name}")

    def generate_random_payload(self) -> dict:
        """Generate a random payload based on discovered model features.

        Uses dynamically discovered feature schemas from MLflow when available,
        falls back to hardcoded credit scoring payload if schema discovery fails.

        Returns
        -------
        dict
            A payload with model inputs in the expected format
        """
        if self._feature_specs:
            return self._payload_generator.generate(self._feature_specs)
        return self._generate_credit_scoring_payload()

    def _generate_credit_scoring_payload(self) -> dict:
        """Generate a hardcoded payload for credit scoring model.

        This is the fallback when schema discovery fails.

        Returns
        -------
        dict
            A payload with credit scoring features
        """
        age = random.randint(22, 70)
        income = random.randint(15000, 150000)
        loan_amount = random.randint(1000, 80000)
        loan_duration_months = random.choice([12, 24, 36, 48, 60, 84])
        credit_score = random.randint(300, 850)
        num_existing_loans = random.randint(0, 6)
        employment_years = random.randint(0, min(35, age - 18))
        missed_payments_12m = random.randint(0, 5)

        # Derived ratios
        ratio = round(min(loan_amount / income, 5.0), 4)
        debt_to_income_ratio = ratio
        loan_to_income_ratio = ratio

        payload = {
            "inputs": {
                "age": float(age),
                "income": float(income),
                "loan_amount": float(loan_amount),
                "loan_duration_months": float(loan_duration_months),
                "credit_score": float(credit_score),
                "num_existing_loans": float(num_existing_loans),
                "employment_years": float(employment_years),
                "missed_payments_12m": float(missed_payments_12m),
                "debt_to_income_ratio": float(debt_to_income_ratio),
                "loan_to_income_ratio": float(loan_to_income_ratio),
            }
        }
        return payload

    def generate_failing_payload(self) -> dict:
        """Generate an intentionally malformed payload that will cause the model to return an error."""
        return {"inputs": {"invalid_field": "this_should_fail"}}

    async def invoke_model(self) -> bool:
        """Make a single invocation to the model endpoint.

        Uses ``success_rate`` to decide whether to send a valid or failing payload.

        Returns
        -------
        bool
            True if the invocation was successful, False otherwise
        """
        try:
            if random.randint(1, 100) <= self.success_rate:
                payload = self.generate_random_payload()
            else:
                payload = self.generate_failing_payload()
            response = requests.post(
                self.endpoint_url, headers={"Content-Type": "application/json"}, json=payload, timeout=10
            )

            self.statistics["total_calls"] += 1
            self.statistics["last_call_time"] = time.time()

            if response.status_code == 200:
                self.statistics["successful_calls"] += 1
                logger.debug(f"✅ Model invocation successful: {response.json()}")
                return True
            else:
                self.statistics["failed_calls"] += 1
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.statistics["last_error"] = error_msg
                logger.warning(f"❌ Model invocation failed: {error_msg}")
                return False

        except requests.exceptions.RequestException as e:
            self.statistics["failed_calls"] += 1
            error_msg = f"Request error: {str(e)}"
            self.statistics["last_error"] = error_msg
            logger.error(f"⚠️ Exception during model invocation: {error_msg}")
            return False

    async def run_simulation(self):
        """Run the simulation loop with duration limit.

        Makes k concurrent requests per round, waits a random interval (0.1-5s),
        then repeats until duration expires.
        """
        logger.info(f"🚀 Starting user behavior simulation for {self.project_name}/{self.model_name}")
        logger.info(f"   Endpoint: {self.endpoint_url}")
        logger.info(f"   Duration: {self.duration_minutes}m")
        logger.info(f"   Users per round: {self.num_users}")
        logger.info("   Random interval: 0.1-5.0s between rounds")

        self.is_running = True
        start_time = time.time()
        duration_seconds = self.duration_minutes * 60

        try:
            while self.is_running:
                elapsed = time.time() - start_time
                if elapsed >= duration_seconds:
                    logger.info(f"Duration limit ({self.duration_minutes}m) reached")
                    break

                # Round: make k concurrent invocations
                tasks = [asyncio.create_task(self.invoke_model()) for _ in range(self.num_users)]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Generate random interval between 0.1 and 5.0 seconds
                interval = random.uniform(0.1, 5.0)
                logger.debug(f"Waiting {interval:.2f}s before next round")

                if self.is_running:
                    await asyncio.sleep(interval)
        finally:
            self.is_running = False
            logger.info(f"⏹️  Stopped user behavior simulation for " f"{self.project_name}/{self.model_name}")

    async def start(self):
        """Start the simulation with multiple concurrent rounds."""
        if self.is_running:
            logger.warning(f"Simulation already running for {self.project_name}/{self.model_name}")
            return

        self.stop_event.clear()
        self.tasks = [asyncio.create_task(self.run_simulation())]
        logger.info(
            f"Simulation started with {self.num_users} user(s) per round for " f"{self.project_name}/{self.model_name}"
        )

    async def stop(self):
        """Stop the simulation."""
        if not self.is_running:
            logger.warning(f"Simulation not running for {self.project_name}/{self.model_name}")
            return

        self.is_running = False
        self.stop_event.set()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info(f"Simulation stopped for {self.project_name}/{self.model_name}")

    def get_statistics(self) -> dict:
        """Get statistics about the simulation.

        Returns
        -------
        dict
            Dictionary containing call statistics
        """
        return {
            "simulation_id": self.simulation_id,
            "project_name": self.project_name,
            "model_name": self.model_name,
            "is_running": self.is_running,
            "endpoint_url": self.endpoint_url,
            "duration_minutes": self.duration_minutes,
            "num_users": self.num_users,
            "success_rate": self.success_rate,
            "random_interval": "0.1-5.0s per round",
            "total_calls": self.statistics["total_calls"],
            "successful_calls": self.statistics["successful_calls"],
            "failed_calls": self.statistics["failed_calls"],
            "last_call_time": self.statistics["last_call_time"],
            "last_error": self.statistics["last_error"],
        }


class SimulationManager:
    """Manages multiple user behavior simulations."""

    def __init__(self):
        """Initialize the simulation manager."""
        self.simulations: dict[str, UserBehaviorSimulator] = {}  # simulation_id -> simulator

    async def start_simulation(
        self,
        project_name: str,
        model_name: str,
        duration_minutes: int = 5,
        num_users: int = 1,
        success_rate: int = 100,
    ) -> dict:
        """Start a new simulation.

        Parameters
        ----------
        project_name : str
            The project name
        model_name : str
            The model name
        duration_minutes : int
            Duration in minutes (1-10, default: 5)
        num_users : int
            Number of concurrent users per round (default: 1)
        success_rate : int
            Percentage of calls that should succeed (0-100, default: 100)

        Returns
        -------
        dict
            Status information with simulation_id and simulator details

        Raises
        ------
        ValueError
            If the model deployment is not found in the project
        """
        try:
            simulator = UserBehaviorSimulator(
                project_name,
                model_name,
                duration_minutes=duration_minutes,
                num_users=num_users,
                success_rate=success_rate,
            )
            await simulator.start()
            simulation_id = simulator.simulation_id
            self.simulations[simulation_id] = simulator
            logger.info(f"Started new simulation {simulation_id} for {project_name}/{model_name}")
            return {"status": "started", "simulation_id": simulation_id, "simulation": simulator.get_statistics()}
        except ValueError as e:
            logger.error(f"Failed to start simulation: {e}")
            raise

    async def stop_simulation(self, simulation_id: str) -> dict:
        """Stop a running simulation.

        Parameters
        ----------
        simulation_id : str
            The unique simulation ID

        Returns
        -------
        dict
            Status information about the stopped simulation
        """
        if simulation_id not in self.simulations:
            logger.warning(f"No simulation found with ID {simulation_id}")
            return {"status": "not_found", "message": f"No simulation found with ID {simulation_id}"}

        simulator = self.simulations[simulation_id]
        await simulator.stop()
        logger.info(f"Stopped simulation {simulation_id}")
        return {"status": "stopped", "simulation": simulator.get_statistics()}

    async def restart_simulation(self, simulation_id: str) -> dict:
        """Restart a terminated simulation with the same parameters.

        Parameters
        ----------
        simulation_id : str
            The ID of the simulation to restart

        Returns
        -------
        dict
            Status information about the restarted simulation
        """
        if simulation_id not in self.simulations:
            raise ValueError(f"No simulation found with ID {simulation_id}")

        old_simulator = self.simulations[simulation_id]

        # Check if already running
        if old_simulator.is_running:
            raise ValueError(f"Simulation {simulation_id} is still running")

        # Extract parameters from old simulator
        project_name = old_simulator.project_name
        model_name = old_simulator.model_name
        duration_minutes = old_simulator.duration_minutes
        num_users = old_simulator.num_users
        success_rate = old_simulator.success_rate

        # Remove the old simulator
        del self.simulations[simulation_id]

        # Start a new simulation with the same parameters
        result = await self.start_simulation(
            project_name=project_name,
            model_name=model_name,
            duration_minutes=duration_minutes,
            num_users=num_users,
            success_rate=success_rate,
        )
        return result

    def list_simulations(self) -> dict:
        """List all simulations with their status.

        Returns
        -------
        dict
            Dictionary with simulations list
        """
        simulations_list = [simulator.get_statistics() for simulator in self.simulations.values()]
        return {"simulations": simulations_list}
