"""LangGraph ReAct agent for the weather assistant, packaged as an MLflow ResponsesAgent.

Stateless: the conversation history is provided by the caller in each request.
The platform handles tracing (mlflow.langchain.autolog) and registration externally.

Simpler than the e-commerce agent on purpose: single ReAct loop, no reflection node —
this is the "minimal viable agent" shape used to validate that the platform's
register/deploy/govern pipeline is generic, not tailored to the SQL agent.
"""

import os
import uuid
from typing import Annotated, TypedDict

import mlflow
from config import (
    MAMMOUTH_AGENT_MODEL,
    MAMMOUTH_API_KEY,
    MAMMOUTH_BASE_URL,
    MAMMOUTH_TEMPERATURE,
    WEATHER_API_KEY,
    WEATHER_BASE_URL,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
from prompts import AGENT_SYSTEM_PROMPT
from tools import make_tools

# Enable LangChain auto-tracing when MLFLOW_TRACKING_URI is set.
if os.environ.get("MLFLOW_TRACKING_URI"):
    mlflow.set_experiment(os.environ.get("MLFLOW_EXPERIMENT_NAME", "weather_assistant_exp"))
    mlflow.langchain.autolog()


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


class WeatherAgent(ResponsesAgent):
    """Weather assistant using a plain LangGraph ReAct loop (no reflection)."""

    def __init__(self):
        tools = make_tools(WEATHER_API_KEY, WEATHER_BASE_URL)
        self.llm = ChatOpenAI(
            model=MAMMOUTH_AGENT_MODEL,
            temperature=MAMMOUTH_TEMPERATURE,
            api_key=MAMMOUTH_API_KEY,
            base_url=MAMMOUTH_BASE_URL,
        ).bind_tools(tools)
        self.app = self._build_graph(tools)

    # ── Graph ─────────────────────────────────────────────────────────────────

    def _build_graph(self, tools: list):
        def agent_node(state: AgentState) -> dict:
            messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)] + state["messages"]
            response = self.llm.invoke(messages)
            return {"messages": [response]}

        def should_continue(state: AgentState) -> str:
            return "tools" if state["messages"][-1].tool_calls else END

        graph = StateGraph(AgentState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", ToolNode(tools))

        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", should_continue)
        graph.add_edge("tools", "agent")
        return graph.compile()

    # ── MLflow ResponsesAgent interface ───────────────────────────────────────

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """Process one user turn given the full conversation history in request.input."""
        messages = self._convert_input_to_langchain_messages(request.input)

        result = self.app.invoke(
            {"messages": messages},
            config={"recursion_limit": 25},
        )

        response_text = next(
            m.content for m in reversed(result["messages"]) if isinstance(m, AIMessage) and not m.tool_calls
        )

        return ResponsesAgentResponse(
            output=[
                {
                    "id": f"msg_{uuid.uuid4().hex}",
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": response_text}],
                }
            ],
        )

    @staticmethod
    def _convert_input_to_langchain_messages(input_messages: list) -> list:
        """Convert OpenAI Responses API messages to LangChain messages.

        Handles both dicts and pydantic Message objects (MLflow passes the latter
        during signature validation).
        """
        converted = []
        for msg in input_messages:
            data = msg.model_dump() if hasattr(msg, "model_dump") else msg
            role = data.get("role")
            content = data.get("content", "")

            if isinstance(content, list):
                content = " ".join(
                    (part.get("text", "") if isinstance(part, dict) else getattr(part, "text", "")) for part in content
                )

            if role == "user":
                converted.append(HumanMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            elif role == "system":
                converted.append(SystemMessage(content=content))
        return converted


mlflow.models.set_model(WeatherAgent())
