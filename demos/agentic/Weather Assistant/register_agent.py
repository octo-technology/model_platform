"""Register the weather assistant agent into a platform project's MLflow registry.

Usage:
    PROJECT_NAME=Credit-Risk-Assessment python register_agent.py

Defaults the tracking URI to http://model-platform.com/registry/{PROJECT_NAME}/
(same convention as demos/agentic/Ecommerce Text2SQL/register_agent.py).

The model_type=agent tag is what the platform's agent sync uses to discover agents.
This agent is deliberately simpler than the e-commerce one (single ReAct loop, no
reflection, no DB) and used a different secret (WEATHER_API_KEY instead of a DB
password) — it exists to validate that register/deploy/govern works for a second,
unrelated agent without touching platform code.

The `deployment_config.json` artifact (logged on the run, so it's per-version) carries
non-secret deployment config (LLM base URL/model, weather API base URL) that the
platform injects as plain env vars when deploying this agent to K8s. Secrets
(MAMMOUTH_API_KEY, WEATHER_API_KEY) are NOT part of it — they're supplied at deploy
time via the platform's UI/CLI (`mp agent deploy-agent --secret KEY=VALUE`), which
pushes them straight to a K8s Secret and never persists them.
"""

import json
import os
import re
import sys
from pathlib import Path

import mlflow
from mlflow import MlflowClient

# This script lives inside the model_platform monorepo (a uv project), so MLflow's
# uv-project autodetection would otherwise copy the whole backend's uv.lock/pyproject.toml
# into this agent's run artifacts. Disable it — the platform's Docker build only ever
# reads requirements.txt (derived from PIP_REQUIREMENTS below), never these files.
os.environ.setdefault("MLFLOW_LOG_UV_FILES", "false")

# Make this script runnable from anywhere by resolving paths relative to the file.
_DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DEMO_DIR)

from config import MAMMOUTH_AGENT_MODEL, MAMMOUTH_BASE_URL, MAMMOUTH_TEMPERATURE, WEATHER_BASE_URL  # noqa: E402
from prompts import AGENT_SYSTEM_PROMPT  # noqa: E402

MODEL_NAME = "weather_assistant"
EXPERIMENT_NAME = "weather_assistant_exp"

DESCRIPTION = (
    "Assistant météo conversationnel. Reçoit une question en langage naturel (français), "
    "récupère la météo actuelle d'une ville via une API tierce et répond de façon synthétique. "
    "Architecture ReAct LangGraph simple (sans boucle de réflexion)."
)

TOOLS = [
    {
        "name": "get_current_weather",
        "description": "Retourne la météo actuelle d'une ville (température, description, humidité, vent).",
    },
    {
        "name": "convert_temperature",
        "description": "Convertit une température entre Celsius, Fahrenheit et Kelvin.",
    },
]

GUARDRAILS = {
    "read_only_external_call": "get_current_weather n'effectue qu'un GET vers l'API météo, aucune écriture",
    "recursion_limit": 25,
}

# Non-secret deployment config, logged as a per-run (per-version) artifact and
# injected as plain env vars by the platform at deploy time. WEATHER_API_KEY and
# MAMMOUTH_API_KEY are deliberately excluded — see module docstring.
DEPLOYMENT_CONFIG = {
    "MAMMOUTH_BASE_URL": MAMMOUTH_BASE_URL,
    "MAMMOUTH_AGENT_MODEL": MAMMOUTH_AGENT_MODEL,
    "MAMMOUTH_TEMPERATURE": str(MAMMOUTH_TEMPERATURE),
    "WEATHER_BASE_URL": WEATHER_BASE_URL,
}

PIP_REQUIREMENTS = [
    "mlflow>=3.0",
    "langchain",
    "langchain-openai",
    "langgraph",
    "requests",
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

    agent_card_text = (Path(_DEMO_DIR) / "agent_card.md").read_text(encoding="utf-8")

    with mlflow.start_run(run_name=f"register-{MODEL_NAME}") as run:
        # ── Hyperparamètres ───────────────────────────────────────────────────
        mlflow.log_params(
            {
                "llm_model": MAMMOUTH_AGENT_MODEL,
                "llm_provider": "mammouth",
                "llm_base_url": MAMMOUTH_BASE_URL,
                "temperature": MAMMOUTH_TEMPERATURE,
                "max_iterations": 1,
                "recursion_limit": 25,
            }
        )

        # ── Tags — identification ─────────────────────────────────────────────
        mlflow.set_tag("model_type", "agent")
        mlflow.set_tag("framework", "langgraph")
        mlflow.set_tag("agent_type", "react_simple")

        # ── Tags — configuration LLM et outils ────────────────────────────────
        mlflow.set_tag("llm_provider", "mammouth")
        mlflow.set_tag("llm_model", MAMMOUTH_AGENT_MODEL)
        mlflow.set_tag("tools", json.dumps(TOOLS, ensure_ascii=False))
        mlflow.set_tag("guardrails", json.dumps(GUARDRAILS, ensure_ascii=False))
        mlflow.set_tag("max_iterations", "1")

        # ── Tags — données accédées ────────────────────────────────────────────
        mlflow.set_tag("data_source", "API météo tierce (OpenWeatherMap, lecture seule)")
        mlflow.set_tag("data_language", "FR")
        mlflow.set_tag("contains_personal_data", "non — aucune donnée personnelle traitée")

        # ── Tags — AI Act ─────────────────────────────────────────────────────
        mlflow.set_tag("ai_act_risk_level", "minimal")
        mlflow.set_tag(
            "ai_act_article",
            "Aucune obligation spécifique — système à risque minimal (information factuelle non personnelle)",
        )

        # ── Tag — Agent Card (visible comme description dans la UI MLflow) ────
        mlflow.set_tag("mlflow.note.content", agent_card_text)

        # ── Artefacts ─────────────────────────────────────────────────────────
        mlflow.log_artifact(os.path.join(_DEMO_DIR, "agent_card.md"))
        mlflow.log_artifact(os.path.join(_DEMO_DIR, "prompts.py"))
        mlflow.log_text(AGENT_SYSTEM_PROMPT, "prompts/agent_system_prompt.txt")
        # Non-secret deployment config for THIS version — read by the platform via
        # AgentRegistry.get_deployment_config at deploy time.
        mlflow.log_dict(DEPLOYMENT_CONFIG, "deployment_config.json")

        # ── Agent (MLflow 3.x ResponsesAgent, models-from-code) ───────────────
        logged = mlflow.pyfunc.log_model(
            name=MODEL_NAME,
            python_model=os.path.join(_DEMO_DIR, "agent.py"),
            code_paths=[os.path.join(_DEMO_DIR, f) for f in ["config.py", "prompts.py", "tools.py", "__init__.py"]],
            pip_requirements=PIP_REQUIREMENTS,
            input_example={"input": [{"role": "user", "content": "Quelle est la météo à Lyon ?"}]},
        )
        print(f"Logged model URI: {logged.model_uri}")
        print(f"Run ID: {run.info.run_id}")

    version = mlflow.register_model(logged.model_uri, name=MODEL_NAME)
    print(f"Registered {MODEL_NAME} v{version.version}")

    # ── Registered model tags (partagés entre versions, lus par la MP) ────────
    client = MlflowClient(tracking_uri=tracking_uri)
    client.update_registered_model(name=MODEL_NAME, description=DESCRIPTION)
    client.set_registered_model_tag(MODEL_NAME, "model_type", "agent")
    client.set_registered_model_tag(MODEL_NAME, "description", DESCRIPTION)
    client.set_registered_model_tag(MODEL_NAME, "agent_type", "react_simple")
    client.set_registered_model_tag(MODEL_NAME, "llm_provider", "mammouth")
    client.set_registered_model_tag(MODEL_NAME, "llm_model", MAMMOUTH_AGENT_MODEL)
    client.set_registered_model_tag(MODEL_NAME, "ai_act_risk_level", "minimal")
    client.set_registered_model_tag(MODEL_NAME, "tools", json.dumps(TOOLS, ensure_ascii=False))
    client.set_registered_model_tag(MODEL_NAME, "guardrails", json.dumps(GUARDRAILS, ensure_ascii=False))
    client.set_registered_model_tag(MODEL_NAME, "max_iterations", "1")
    print(f"Tagged {MODEL_NAME} with model_type=agent and full metadata")
    # Secret name must match K8SAgentDeployment.secret_name (sanitize_project_name on both parts).
    sanitized_secret_name = re.sub(r"[^a-z0-9-]", "-", f"{project_name}-{MODEL_NAME}-secrets".lower())
    print(
        f"Reminder: create the K8s Secret before deploying — "
        f"kubectl create secret generic {sanitized_secret_name} -n <namespace> "
        f"--from-literal=MAMMOUTH_API_KEY=... --from-literal=WEATHER_API_KEY=..."
    )


if __name__ == "__main__":
    main()
