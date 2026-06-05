"""Streamlit chat client for the e-commerce agent deployed on the Model Platform.

Does NOT instantiate the agent locally. POSTs the conversation history to the
platform's `/agent_predict` endpoint and renders the Responses API JSON output.
The deployed agent is stateless; the conversation is kept client-side.

Run from the model_platform repo root:
    uv run streamlit run "demos/agentic/Ecommerce Text2SQL/streamlit_chat.py"
"""

import json
from typing import Any

import requests
import streamlit as st

DEFAULT_PROJECT = "Credit-Risk-Assessment"
DEFAULT_DEPLOYMENT = "credit-risk-assessment-ecommerce-text2sql-3-deployment-a3fadb"
DEFAULT_PLATFORM = "http://model-platform.com"
REQUEST_TIMEOUT_S = 120


# ── Helpers ─────────────────────────────────────────────────────────────────


def build_endpoint(platform: str, project: str, deployment: str) -> str:
    return f"{platform.rstrip('/')}/deploy/{project}/{deployment}/agent_predict"


def build_mlflow_url(platform: str, project: str) -> str:
    return f"{platform.rstrip('/')}/registry/{project}/"


def call_agent(endpoint: str, messages: list[dict]) -> tuple[str, dict]:
    """POST the message history to the deployed agent and return (text, raw_json).

    Raises requests.RequestException on transport errors; the caller handles them.
    """
    payload = {"input": [{"role": m["role"], "content": m["content"]} for m in messages]}
    response = requests.post(endpoint, json=payload, timeout=REQUEST_TIMEOUT_S)
    response.raise_for_status()
    data = response.json()

    # Responses API output: data["output"][0]["content"][0]["text"]
    text = ""
    try:
        first = data["output"][0]
        content = first.get("content", [])
        if isinstance(content, list) and content:
            text = content[0].get("text", "")
        elif isinstance(content, str):
            text = content
    except (KeyError, IndexError, TypeError):
        text = json.dumps(data)
    return text, data


# ── UI ──────────────────────────────────────────────────────────────────────


st.set_page_config(page_title="MP Agent Tester", page_icon="🛰️", layout="wide")
st.title("🛰️ MP Agent Tester")
st.caption("Chat avec l'agent déployé sur la Model Platform — pas d'agent local")


def _init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "platform" not in st.session_state:
        st.session_state.platform = DEFAULT_PLATFORM
    if "project" not in st.session_state:
        st.session_state.project = DEFAULT_PROJECT
    if "deployment" not in st.session_state:
        st.session_state.deployment = DEFAULT_DEPLOYMENT
    if "last_raw_response" not in st.session_state:
        st.session_state.last_raw_response = None


_init_state()


# ── Sidebar config ──────────────────────────────────────────────────────────


with st.sidebar:
    st.subheader("Configuration du déploiement")
    st.session_state.platform = st.text_input("Platform URL", st.session_state.platform)
    st.session_state.project = st.text_input("Projet", st.session_state.project)
    st.session_state.deployment = st.text_input("Deployment name", st.session_state.deployment)

    endpoint = build_endpoint(st.session_state.platform, st.session_state.project, st.session_state.deployment)
    st.caption("Endpoint :")
    st.code(endpoint, language="text")

    st.markdown("---")
    st.subheader("MLflow")
    st.link_button("Ouvrir le registry", build_mlflow_url(st.session_state.platform, st.session_state.project))

    st.markdown("---")
    if st.button("🗑️ Reset conversation"):
        st.session_state.messages = []
        st.session_state.last_raw_response = None
        st.rerun()

    if st.session_state.last_raw_response is not None:
        with st.expander("Dernière réponse brute"):
            st.json(st.session_state.last_raw_response)


# ── Chat ────────────────────────────────────────────────────────────────────


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_prompt = st.chat_input("Posez votre question à l'agent…")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent en cours d'inférence…"):
            try:
                text, raw = call_agent(endpoint, st.session_state.messages)
                st.session_state.last_raw_response = raw
                st.markdown(text)
                st.session_state.messages.append({"role": "assistant", "content": text})
            except requests.HTTPError as exc:
                err: dict[str, Any] = {}
                try:
                    err = exc.response.json()
                except Exception:
                    err = {"raw": exc.response.text if exc.response is not None else str(exc)}
                st.error(f"HTTP {exc.response.status_code if exc.response else '?'} — {err}")
                st.session_state.last_raw_response = err
            except requests.RequestException as exc:
                st.error(f"Erreur réseau : {exc}")
                st.session_state.last_raw_response = {"error": str(exc)}
