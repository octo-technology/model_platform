"""Register the e-commerce text2sql agent into a platform project's MLflow registry.

Usage:
    PROJECT_NAME=Credit-Risk-Assessment python register_agent.py

Defaults the tracking URI to http://model-platform.com/registry/{PROJECT_NAME}/
(same convention as the ML notebooks in demos/notebooks/).

The model_type=agent tag is what the platform's agent sync uses to discover agents.
"""

import os
import sys

import mlflow
from mlflow import MlflowClient

# Make this script runnable from anywhere by resolving paths relative to the file.
_DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DEMO_DIR)

from config import MAMMOUTH_AGENT_MODEL, MAMMOUTH_REFLECT_MODEL  # noqa: E402

MODEL_NAME = "ecommerce_text2sql"
EXPERIMENT_NAME = "ecommerce_text2sql_exp"

PIP_REQUIREMENTS = [
    "mlflow>=3.0",
    "langchain",
    "langchain-openai",
    "langgraph",
    "psycopg[binary]",
    "python-dotenv",
]


def main() -> None:
    project_name = os.environ.get("PROJECT_NAME", "Credit-Risk-Assessment")
    tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI",
        f"http://model-platform.com/registry/{project_name}/",
    )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    print(f"MLflow tracking URI : {tracking_uri}", flush=True)

    with mlflow.start_run(run_name=f"register-{MODEL_NAME}") as run:
        logged = mlflow.pyfunc.log_model(
            name=MODEL_NAME,
            python_model=os.path.join(_DEMO_DIR, "agent.py"),
            code_paths=[
                os.path.join(_DEMO_DIR, f)
                for f in [
                    "config.py",
                    "database_adapters.py",
                    "database_utils.py",
                    "prompts.py",
                    "security.py",
                    "tools.py",
                    "__init__.py",
                ]
            ],
            pip_requirements=PIP_REQUIREMENTS,
        )
        print(f"Logged model URI: {logged.model_uri}")
        print(f"Run ID: {run.info.run_id}")

    version = mlflow.register_model(logged.model_uri, name=MODEL_NAME)
    print(f"Registered {MODEL_NAME} v{version.version}")

    client = MlflowClient(tracking_uri=tracking_uri)
    client.set_registered_model_tag(MODEL_NAME, "model_type", "agent")
    client.set_registered_model_tag(MODEL_NAME, "agent_type", "rag")
    client.set_registered_model_tag(MODEL_NAME, "llm_provider", "openai-compatible")
    client.set_registered_model_tag(MODEL_NAME, "llm_model", MAMMOUTH_AGENT_MODEL)
    client.set_registered_model_tag(MODEL_NAME, "reflect_model", MAMMOUTH_REFLECT_MODEL)
    client.set_registered_model_tag(MODEL_NAME, "ai_act_risk_level", "limited")
    print(f"Tagged {MODEL_NAME} with model_type=agent")


if __name__ == "__main__":
    main()
