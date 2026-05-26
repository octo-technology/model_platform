"""Register the e-commerce text2sql agent into the platform's MLflow registry.

Usage:
    export MLFLOW_TRACKING_URI=http://localhost:5000
    python register_agent.py

The model_type=agent tag is what the platform's sync uses to discover agents.
"""

import os

import mlflow
from mlflow import MlflowClient

from .config import MAMMOUTH_AGENT_MODEL, MAMMOUTH_REFLECT_MODEL

MODEL_NAME = "ecommerce_text2sql"
EXPERIMENT_NAME = "agents"

PIP_REQUIREMENTS = [
    "mlflow>=3.0",
    "langchain",
    "langchain-openai",
    "langgraph",
    "psycopg[binary]",
    "python-dotenv",
]


def main() -> None:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name=f"register-{MODEL_NAME}") as run:
        logged = mlflow.pyfunc.log_model(
            name="agent",
            python_model="agent.py",
            code_paths=[
                "config.py",
                "database_adapters.py",
                "database_utils.py",
                "prompts.py",
                "security.py",
                "tools.py",
                "__init__.py",
            ],
            pip_requirements=PIP_REQUIREMENTS,
            input_example={"input": [{"role": "user", "content": "Combien de clients avons-nous ?"}]},
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
