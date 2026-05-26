"""LangGraph ReAct agent for the e-commerce chatbot, packaged as an MLflow ResponsesAgent.

Stateless: the conversation history is provided by the caller in each request.
The platform handles tracing (mlflow.langchain.autolog) and registration externally.
"""

import json
import uuid
from typing import Annotated, TypedDict

import mlflow
from config import (
    MAMMOUTH_AGENT_MODEL,
    MAMMOUTH_API_KEY,
    MAMMOUTH_BASE_URL,
    MAMMOUTH_REFLECT_MODEL,
    MAMMOUTH_TEMPERATURE,
)
from database_adapters import PostgresAdapter
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
from prompts import AGENT_SYSTEM_PROMPT, REFLECTION_SYSTEM_PROMPT
from tools import make_tools

MAX_REFLECTIONS = 2


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    reflection_count: int
    reflection_approved: bool


class ECommerceAgent(ResponsesAgent):
    """E-commerce SQL Agent using an explicit LangGraph ReAct loop with reflection."""

    def __init__(self):
        tools = make_tools(PostgresAdapter())
        self.llm = ChatOpenAI(
            model=MAMMOUTH_AGENT_MODEL,
            temperature=MAMMOUTH_TEMPERATURE,
            api_key=MAMMOUTH_API_KEY,
            base_url=MAMMOUTH_BASE_URL,
        ).bind_tools(tools)
        self.reflection_llm = ChatOpenAI(
            model=MAMMOUTH_REFLECT_MODEL,
            temperature=0,
            api_key=MAMMOUTH_API_KEY,
            base_url=MAMMOUTH_BASE_URL,
        )
        self.app = self._build_graph(tools)

    # ── Graph ─────────────────────────────────────────────────────────────────

    def _build_graph(self, tools: list):
        def agent_node(state: AgentState) -> dict:
            messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)] + state["messages"]
            response = self.llm.invoke(messages)
            return {"messages": [response]}

        def should_continue(state: AgentState) -> str:
            return "tools" if state["messages"][-1].tool_calls else "reflect"

        def reflect_node(state: AgentState) -> dict:
            messages = state["messages"]
            reflection_count = state.get("reflection_count", 0)

            user_question = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")

            sql_pairs = []
            for i, msg in enumerate(messages):
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc["name"] == "execute_sql":
                            query = tc["args"].get("query", "")
                            result = next(
                                (
                                    m.content
                                    for m in messages[i + 1 :]
                                    if isinstance(m, ToolMessage) and m.tool_call_id == tc["id"]
                                ),
                                "(résultat non trouvé)",
                            )
                            sql_pairs.append((query, result))

            final_answer = messages[-1].content

            sql_context = (
                "\n\n".join(f"Requête SQL :\n{q}\n\nRésultat :\n{r}" for q, r in sql_pairs)
                if sql_pairs
                else "Aucune requête SQL exécutée."
            )

            reflection_prompt = (
                f"Question de l'utilisateur :\n{user_question}\n\n"
                f"{sql_context}\n\n"
                f"Réponse finale proposée :\n{final_answer}\n\n"
                "Évalue si la réponse est correcte et complète."
            )

            raw = self.reflection_llm.invoke(
                [
                    SystemMessage(content=REFLECTION_SYSTEM_PROMPT),
                    HumanMessage(content=reflection_prompt),
                ]
            ).content.strip()

            try:
                result = json.loads(raw)
                approved = bool(result.get("approved", False))
                critique = result.get("critique", "")
            except json.JSONDecodeError:
                approved = False
                critique = raw

            next_count = reflection_count + 1
            will_retry = not approved and next_count < MAX_REFLECTIONS

            if will_retry:
                new_messages = [
                    SystemMessage(
                        content=(
                            f"[INSTRUCTION INTERNE] Ta réponse précédente est incorrecte ou incomplète. "
                            f"{critique}. Génère une nouvelle réponse corrigée sans mentionner cette correction."
                        )
                    )
                ]
            elif not approved:
                last_ai = next(
                    (m for m in reversed(messages) if isinstance(m, AIMessage) and not m.tool_calls),
                    None,
                )
                new_messages = []
                if last_ai is not None:
                    new_messages.append(RemoveMessage(id=last_ai.id))
                new_messages.append(
                    AIMessage(
                        content=(
                            "Je n'ai pas réussi à trouver des informations pertinentes pour répondre à votre question. "
                            "Pourriez-vous reformuler ou préciser votre demande ?"
                        )
                    )
                )
            else:
                new_messages = []

            return {
                "messages": new_messages,
                "reflection_count": next_count,
                "reflection_approved": approved,
            }

        def should_accept(state: AgentState) -> str:
            if state.get("reflection_approved", False) or state.get("reflection_count", 0) >= MAX_REFLECTIONS:
                return END
            return "agent"

        graph = StateGraph(AgentState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", ToolNode(tools))
        graph.add_node("reflect", reflect_node)

        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", should_continue)
        graph.add_edge("tools", "agent")
        graph.add_conditional_edges("reflect", should_accept)
        return graph.compile()

    # ── MLflow ResponsesAgent interface ───────────────────────────────────────

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """Process one user turn given the full conversation history in request.input."""
        messages = self._convert_input_to_langchain_messages(request.input)

        result = self.app.invoke(
            {
                "messages": messages,
                "reflection_count": 0,
                "reflection_approved": False,
            },
            config={"recursion_limit": 100},
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
            # Normalize pydantic Message objects to plain dicts
            data = msg.model_dump() if hasattr(msg, "model_dump") else msg
            role = data.get("role")
            content = data.get("content", "")

            # content can be a plain string or a list of {type, text} parts
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


mlflow.models.set_model(ECommerceAgent())
