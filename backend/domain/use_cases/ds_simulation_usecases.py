"""Use cases for Data Scientist behavior simulation.

Simulates a Data Scientist who trains models and pushes them to the platform
via MLflow. Each simulation run generates synthetic data, trains a model with
randomized hyperparameters, and registers the resulting model in the project
registry — mimicking the iterative experimentation cycle of a real DS.
"""

import asyncio
import random
import time
import uuid
from typing import TypedDict

import mlflow
import mlflow.sklearn
import numpy as np
from loguru import logger
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingClassifier  # type: ignore[import-untyped]
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score  # type: ignore[import-untyped]
from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

from backend.utils import sanitize_project_name


class DSSimulationStats(TypedDict):
    """Statistics dictionary for DS simulation tracking."""

    simulation_id: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    last_run_time: float | None
    last_run_id: str | None
    last_error: str | None


CREDIT_FEATURES = [
    "age",
    "income",
    "loan_amount",
    "loan_duration_months",
    "credit_score",
    "num_existing_loans",
    "employment_years",
    "missed_payments_12m",
    "debt_to_income_ratio",
    "loan_to_income_ratio",
]


class DSSimulator:
    """Simulates a Data Scientist pushing model versions to a project MLflow registry.

    Each simulation iteration:
    1. Generates synthetic credit scoring data (random seed → variation each run)
    2. Trains a GradientBoostingClassifier with slightly varied hyperparameters
    3. Logs params, metrics, and the model to MLflow
    4. Registers the model under `model_name` in the project registry

    The interval between pushes and total number of versions are configurable,
    enabling realistic simulation of an iterative DS workflow.
    """

    def __init__(
        self,
        project_name: str,
        model_name: str,
        num_versions: int = 3,
        interval_seconds: int = 60,
    ):
        """Initialize the DS simulator.

        Parameters
        ----------
        project_name : str
            The platform project name — used to derive the MLflow tracking URI
        model_name : str
            The model name to register in MLflow
        num_versions : int
            Number of model versions to push (one per iteration)
        interval_seconds : int
            Wait time between iterations (seconds, minimum 10)
        """
        self.simulation_id: str = str(uuid.uuid4())
        self.project_name: str = project_name
        self.model_name: str = model_name
        self.num_versions: int = max(1, num_versions)
        self.interval_seconds: int = max(10, interval_seconds)
        self.is_running: bool = False

        sanitized = sanitize_project_name(project_name)
        self.tracking_uri = f"http://{sanitized}.{sanitized}.svc.cluster.local:5000"

        self.statistics: DSSimulationStats = {
            "simulation_id": self.simulation_id,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run_time": None,
            "last_run_id": None,
            "last_error": None,
        }

    def _generate_synthetic_data(self, n: int) -> tuple:
        """Generate synthetic credit scoring data.

        Parameters
        ----------
        n : int
            Number of samples to generate

        Returns
        -------
        tuple[ndarray, ndarray]
            Feature matrix X and target vector y
        """
        age = np.random.randint(22, 70, n)
        income = np.random.randint(15_000, 150_000, n)
        loan_amount = np.random.randint(1_000, 80_000, n)
        loan_duration_months = np.random.choice([12, 24, 36, 48, 60, 84], n)
        credit_score = np.random.randint(300, 850, n)
        num_existing_loans = np.random.randint(0, 6, n)
        employment_years = np.random.randint(0, 35, n)
        missed_payments_12m = np.random.randint(0, 5, n)
        debt_to_income_ratio = np.clip(loan_amount / income, 0, 5).round(4)
        loan_to_income_ratio = np.clip(loan_amount / income, 0, 5).round(4)

        log_odds = (
            -3.5
            + 0.008 * np.maximum(0, 35 - age)
            - 0.000012 * income
            + 0.000025 * loan_amount
            - 0.004 * credit_score
            + 0.25 * num_existing_loans
            - 0.04 * employment_years
            + 1.8 * debt_to_income_ratio
            + 0.4 * missed_payments_12m
        )
        prob_default = 1 / (1 + np.exp(-log_odds))
        y = (np.random.rand(n) < prob_default).astype(int)

        features = np.column_stack(
            [
                age,
                income,
                loan_amount,
                loan_duration_months,
                credit_score,
                num_existing_loans,
                employment_years,
                missed_payments_12m,
                debt_to_income_ratio,
                loan_to_income_ratio,
            ]
        )
        return features, y

    def _random_params(self) -> dict:
        """Generate randomized hyperparameters to simulate DS experimentation.

        Returns
        -------
        dict
            GradientBoostingClassifier hyperparameters with controlled variation
        """
        return {
            "n_estimators": random.choice([100, 150, 200, 250]),
            "learning_rate": round(random.uniform(0.03, 0.15), 3),
            "max_depth": random.choice([3, 4, 5]),
            "min_samples_split": random.choice([10, 15, 20, 25]),
            "min_samples_leaf": random.choice([5, 8, 10, 15]),
            "subsample": round(random.uniform(0.7, 1.0), 2),
            "max_features": random.choice(["sqrt", "log2"]),
            "random_state": random.randint(0, 9999),
        }

    def _train_and_log(self) -> str:
        """Generate data, train a model, and log the run to MLflow.

        This is a synchronous, potentially long-running method. It must be
        called via ``run_in_executor`` to avoid blocking the event loop.

        Returns
        -------
        str
            The MLflow run_id of the logged run

        Raises
        ------
        Exception
            If MLflow logging or model registration fails
        """
        np.random.seed(random.randint(0, 99_999))
        n_samples = random.randint(1_500, 3_000)
        params = self._random_params()

        features, y = self._generate_synthetic_data(n=n_samples)
        features_train, features_test, y_train, y_test = train_test_split(
            features, y, test_size=0.2, random_state=42, stratify=y
        )

        scaler = StandardScaler()
        features_train_sc = scaler.fit_transform(features_train)
        features_test_sc = scaler.transform(features_test)

        model = GradientBoostingClassifier(**params)
        model.fit(features_train_sc, y_train)

        y_pred = model.predict(features_test_sc)
        y_proba = model.predict_proba(features_test_sc)[:, 1]

        metrics = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "f1_score": round(float(f1_score(y_test, y_pred)), 4),
            "auc_roc": round(float(roc_auc_score(y_test, y_proba)), 4),
            "default_rate_test": round(float(y_test.mean()), 4),
            "train_size": int(len(features_train)),
            "test_size": int(len(features_test)),
        }

        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.model_name)

        with mlflow.start_run(run_name=f"{self.model_name}_sim") as run:
            mlflow.log_params(params)
            mlflow.log_param("scaler", "StandardScaler")
            mlflow.log_param("features", ", ".join(CREDIT_FEATURES))
            mlflow.log_metrics(metrics)
            mlflow.set_tag("simulated_by", "ds_simulation")
            mlflow.set_tag("simulation_id", self.simulation_id)
            mlflow.set_tag("project_name", self.project_name)
            mlflow.set_tag("model_type", "GradientBoostingClassifier")
            mlflow.set_tag("framework", "scikit-learn")
            mlflow.set_tag("environment", "staging")

            signature = infer_signature(features_train_sc, model.predict_proba(features_train_sc))
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="custom_model",
                registered_model_name=self.model_name,
                signature=signature,
                input_example=features_train_sc[:3],
            )
            return run.info.run_id

    async def run_simulation(self):
        """Push ``num_versions`` model versions to MLflow, one per iteration.

        Waits ``interval_seconds`` between each push. The loop exits early
        if the simulator is stopped via ``stop()``.
        """
        self.is_running = True
        logger.info(
            f"🎓 DS simulation {self.simulation_id} started: "
            f"{self.project_name}/{self.model_name} — "
            f"{self.num_versions} versions, {self.interval_seconds}s interval"
        )
        logger.info(f"   Tracking URI: {self.tracking_uri}")

        try:
            for i in range(self.num_versions):
                if not self.is_running:
                    logger.info(f"DS simulation {self.simulation_id} interrupted at version {i + 1}")
                    break

                self.statistics["total_runs"] += 1
                self.statistics["last_run_time"] = time.time()

                try:
                    run_id = await asyncio.get_event_loop().run_in_executor(None, self._train_and_log)
                    self.statistics["successful_runs"] += 1
                    self.statistics["last_run_id"] = run_id
                    logger.info(
                        f"✅ DS sim {self.simulation_id}: "
                        f"version {i + 1}/{self.num_versions} pushed — run_id={run_id[:8]}..."
                    )
                except Exception as e:
                    self.statistics["failed_runs"] += 1
                    self.statistics["last_error"] = str(e)
                    logger.error(f"❌ DS sim {self.simulation_id}: version {i + 1} failed — {e}")

                if self.is_running and i < self.num_versions - 1:
                    await asyncio.sleep(self.interval_seconds)
        finally:
            self.is_running = False
            logger.info(
                f"⏹️  DS simulation {self.simulation_id} finished — "
                f"{self.statistics['successful_runs']}/{self.statistics['total_runs']} successful"
            )

    async def start(self):
        """Start the DS simulation as a background task."""
        if self.is_running:
            logger.warning(f"DS simulation {self.simulation_id} is already running")
            return
        asyncio.create_task(self.run_simulation())

    async def stop(self):
        """Interrupt the simulation after the current run completes."""
        self.is_running = False
        logger.info(f"DS simulation {self.simulation_id} stop requested")

    def get_statistics(self) -> dict:
        """Return a serializable snapshot of the simulation state.

        Returns
        -------
        dict
            Simulation parameters, current status, and runtime statistics
        """
        return {
            "simulation_id": self.simulation_id,
            "project_name": self.project_name,
            "model_name": self.model_name,
            "num_versions": self.num_versions,
            "interval_seconds": self.interval_seconds,
            "is_running": self.is_running,
            "tracking_uri": self.tracking_uri,
            **self.statistics,
        }


class DSSimulationManager:
    """Manages multiple Data Scientist simulations."""

    def __init__(self):
        """Initialize the DS simulation manager."""
        self.simulations: dict[str, DSSimulator] = {}  # simulation_id -> simulator

    async def start_simulation(
        self,
        project_name: str,
        model_name: str,
        num_versions: int = 3,
        interval_seconds: int = 60,
    ) -> dict:
        """Start a new DS simulation.

        Parameters
        ----------
        project_name : str
            The platform project name
        model_name : str
            The model name to register in MLflow
        num_versions : int
            Number of model versions to push (1-20)
        interval_seconds : int
            Wait time between versions (minimum 10s)

        Returns
        -------
        dict
            Status and simulation details including the simulation_id
        """
        simulator = DSSimulator(
            project_name=project_name,
            model_name=model_name,
            num_versions=num_versions,
            interval_seconds=interval_seconds,
        )
        await simulator.start()
        self.simulations[simulator.simulation_id] = simulator
        logger.info(f"DS simulation {simulator.simulation_id} registered for {project_name}/{model_name}")
        return {"status": "started", "simulation_id": simulator.simulation_id, "simulation": simulator.get_statistics()}

    async def stop_simulation(self, simulation_id: str) -> dict:
        """Interrupt a running DS simulation.

        Parameters
        ----------
        simulation_id : str
            The unique simulation ID

        Returns
        -------
        dict
            Status and final statistics
        """
        if simulation_id not in self.simulations:
            raise ValueError(f"No DS simulation found with ID {simulation_id}")

        simulator = self.simulations[simulation_id]
        await simulator.stop()
        return {"status": "stopped", "simulation": simulator.get_statistics()}

    async def restart_simulation(self, simulation_id: str) -> dict:
        """Restart a completed DS simulation with the same parameters.

        Parameters
        ----------
        simulation_id : str
            The ID of the simulation to restart

        Returns
        -------
        dict
            Status and new simulation details

        Raises
        ------
        ValueError
            If the simulation is not found or is still running
        """
        if simulation_id not in self.simulations:
            raise ValueError(f"No DS simulation found with ID {simulation_id}")

        old = self.simulations[simulation_id]
        if old.is_running:
            raise ValueError(f"DS simulation {simulation_id} is still running")

        project_name = old.project_name
        model_name = old.model_name
        num_versions = old.num_versions
        interval_seconds = old.interval_seconds
        del self.simulations[simulation_id]
        return await self.start_simulation(
            project_name=project_name,
            model_name=model_name,
            num_versions=num_versions,
            interval_seconds=interval_seconds,
        )

    def list_simulations(self) -> dict:
        """List all DS simulations with their current status.

        Returns
        -------
        dict
            Dictionary with a ``simulations`` list
        """
        return {"simulations": [sim.get_statistics() for sim in self.simulations.values()]}
