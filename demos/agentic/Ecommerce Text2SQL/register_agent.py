"""Register the e-commerce text2sql agent into a platform project's MLflow registry.

Usage:
    PROJECT_NAME=Credit-Risk-Assessment python register_agent.py

Defaults the tracking URI to http://model-platform.com/registry/{PROJECT_NAME}/
(same convention as the ML notebooks in demos/notebooks/).

The model_type=agent tag is what the platform's agent sync uses to discover agents.
All agent-specific metadata (agent card, tools, guardrails, LLM config, AI Act risk)
is attached to the run so it shows up in the MLflow UI and gets picked up by the sync.
"""

import json
import os
import sys
from pathlib import Path

import mlflow
from mlflow import MlflowClient

# Make this script runnable from anywhere by resolving paths relative to the file.
_DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DEMO_DIR)

from agent import MAX_REFLECTIONS  # noqa: E402
from config import (  # noqa: E402
    MAMMOUTH_AGENT_MODEL,
    MAMMOUTH_BASE_URL,
    MAMMOUTH_REFLECT_MODEL,
    MAMMOUTH_TEMPERATURE,
)
from prompts import AGENT_SYSTEM_PROMPT, REFLECTION_SYSTEM_PROMPT  # noqa: E402

MODEL_NAME = "ecommerce_text2sql"
EXPERIMENT_NAME = "ecommerce_text2sql_exp"

DESCRIPTION = (
    "Agent conversationnel d'analyse de données e-commerce. Reçoit une question "
    "en langage naturel (français), génère et exécute une requête SQL en lecture "
    "seule, puis formule une réponse synthétique. Architecture ReAct LangGraph avec "
    "boucle de réflexion bornée."
)

TOOLS = [
    {
        "name": "get_schema",
        "description": "Retourne le schéma complet de la base (tables, colonnes, types).",
    },
    {
        "name": "execute_sql",
        "description": "Exécute une requête SQL en lecture seule et retourne les résultats formatés.",
    },
]

GUARDRAILS = {
    "sql_read_only": "Whitelist SELECT/WITH + blacklist DML/DDL via security.is_read_only_query",
    "reflection_loop": f"LLM reviewer with max {MAX_REFLECTIONS} retries",
    "recursion_limit": 100,
}

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
    print("Setting experiment...", flush=True)
    mlflow.set_experiment(EXPERIMENT_NAME)
    print(f"MLflow tracking URI : {tracking_uri}", flush=True)

    agent_card_text = (Path(_DEMO_DIR) / "agent_card.md").read_text(encoding="utf-8")

    with mlflow.start_run(run_name=f"register-{MODEL_NAME}") as run:
        # ── Hyperparamètres ───────────────────────────────────────────────────
        mlflow.log_params(
            {
                "llm_model": MAMMOUTH_AGENT_MODEL,
                "reflect_llm_model": MAMMOUTH_REFLECT_MODEL,
                "llm_provider": "mammouth",
                "llm_base_url": MAMMOUTH_BASE_URL,
                "temperature": MAMMOUTH_TEMPERATURE,
                "reflect_temperature": 0,
                "max_iterations": MAX_REFLECTIONS,
                "recursion_limit": 100,
            }
        )

        # ── Tags — identification ─────────────────────────────────────────────
        mlflow.set_tag("model_type", "agent")
        mlflow.set_tag("framework", "langgraph")
        mlflow.set_tag("agent_type", "react_with_reflection")

        # ── Tags — configuration LLM et outils ────────────────────────────────
        mlflow.set_tag("llm_provider", "mammouth")
        mlflow.set_tag("llm_model", MAMMOUTH_AGENT_MODEL)
        mlflow.set_tag("reflect_llm_model", MAMMOUTH_REFLECT_MODEL)
        mlflow.set_tag("tools", json.dumps(TOOLS, ensure_ascii=False))
        mlflow.set_tag("guardrails", json.dumps(GUARDRAILS, ensure_ascii=False))
        mlflow.set_tag("max_iterations", str(MAX_REFLECTIONS))

        # ── Tags — données accédées ───────────────────────────────────────────
        mlflow.set_tag("data_source", "PostgreSQL e-commerce (read-only via SELECT/WITH)")
        mlflow.set_tag("data_language", "FR (questions) / EN (valeurs en base)")
        mlflow.set_tag(
            "contains_personal_data",
            "indirect — IDs techniques uniquement, aucune PII directe exposée",
        )

        # ── Tags — AI Act ─────────────────────────────────────────────────────
        mlflow.set_tag("ai_act_risk_level", "limited")
        mlflow.set_tag(
            "ai_act_article",
            "Art. 50 — obligations de transparence pour agents conversationnels",
        )

        # ── Tag — Agent Card (visible comme description dans la UI MLflow) ────
        mlflow.set_tag("mlflow.note.content", agent_card_text)

        # ── Artefacts ─────────────────────────────────────────────────────────
        mlflow.log_artifact(os.path.join(_DEMO_DIR, "agent_card.md"))
        mlflow.log_artifact(os.path.join(_DEMO_DIR, "prompts.py"))
        mlflow.log_artifact(os.path.join(_DEMO_DIR, "security.py"))
        # System prompts en texte brut pour audit
        mlflow.log_text(AGENT_SYSTEM_PROMPT, "prompts/agent_system_prompt.txt")
        mlflow.log_text(REFLECTION_SYSTEM_PROMPT, "prompts/reflection_system_prompt.txt")

        # ── Agent (MLflow 3.x ResponsesAgent, models-from-code) ───────────────
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
            input_example={"input": [{"role": "user", "content": "Combien de clients ont commandé en mai 2025 ?"}]},
        )
        print(f"Logged model URI: {logged.model_uri}")
        print(f"Run ID: {run.info.run_id}")

    version = mlflow.register_model(logged.model_uri, name=MODEL_NAME)
    print(f"Registered {MODEL_NAME} v{version.version}")

    # ── Registered model tags (partagés entre versions, lus par la MP) ────────
    # La MP synchronise AgentInfo depuis ces tags via sync_agent_infos_for_project.
    client = MlflowClient(tracking_uri=tracking_uri)
    client.update_registered_model(name=MODEL_NAME, description=DESCRIPTION)
    client.set_registered_model_tag(MODEL_NAME, "model_type", "agent")
    client.set_registered_model_tag(MODEL_NAME, "description", DESCRIPTION)
    client.set_registered_model_tag(MODEL_NAME, "agent_type", "react_with_reflection")
    client.set_registered_model_tag(MODEL_NAME, "llm_provider", "mammouth")
    client.set_registered_model_tag(MODEL_NAME, "llm_model", MAMMOUTH_AGENT_MODEL)
    client.set_registered_model_tag(MODEL_NAME, "reflect_model", MAMMOUTH_REFLECT_MODEL)
    client.set_registered_model_tag(MODEL_NAME, "ai_act_risk_level", "limited")
    client.set_registered_model_tag(MODEL_NAME, "tools", json.dumps(TOOLS, ensure_ascii=False))
    client.set_registered_model_tag(MODEL_NAME, "guardrails", json.dumps(GUARDRAILS, ensure_ascii=False))
    client.set_registered_model_tag(MODEL_NAME, "max_iterations", str(MAX_REFLECTIONS))
    print(f"Tagged {MODEL_NAME} with model_type=agent and full metadata")


if __name__ == "__main__":
    main()
