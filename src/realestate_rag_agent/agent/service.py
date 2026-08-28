"""Run the LangGraph agent for one user message."""

import json
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from sqlalchemy.orm import Session

from realestate_rag_agent.agent.graph import get_agent_graph
from realestate_rag_agent.agent.tools import SESSION_CONFIG_KEY
from realestate_rag_agent.core.config import get_settings


@dataclass
class ToolCallInfo:
    name: str
    args: dict


@dataclass
class AgentResult:
    thread_id: str
    reply: str
    tool_calls: list[ToolCallInfo] = field(default_factory=list)
    properties: list[dict] = field(default_factory=list)


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def _properties_from_tool_message(msg: ToolMessage, into: list[dict], seen: set[str]) -> None:
    try:
        payload = json.loads(msg.content)
    except (json.JSONDecodeError, TypeError):
        return
    if isinstance(payload, dict):
        items = payload["items"] if isinstance(payload.get("items"), list) else [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        return
    for item in items:
        if isinstance(item, dict) and item.get("id") and item["id"] not in seen:
            seen.add(item["id"])
            into.append(item)


def _config(thread_id: str, session: Session) -> dict:
    return {
        "configurable": {"thread_id": thread_id, SESSION_CONFIG_KEY: session},
        "recursion_limit": get_settings().agent_recursion_limit,
    }


def run_agent(session: Session, message: str, thread_id: str | None = None) -> AgentResult:
    thread_id = thread_id or str(uuid.uuid4())
    graph = get_agent_graph()

    state = graph.invoke({"messages": [HumanMessage(message)]}, config=_config(thread_id, session))

    properties: list[dict] = []
    seen: set[str] = set()
    tool_calls: list[ToolCallInfo] = []
    for msg in state["messages"]:
        if isinstance(msg, AIMessage):
            for call in msg.tool_calls or []:
                tool_calls.append(ToolCallInfo(name=call["name"], args=call["args"]))
        elif isinstance(msg, ToolMessage):
            _properties_from_tool_message(msg, properties, seen)

    return AgentResult(
        thread_id=thread_id,
        reply=_text(state["messages"][-1].content),
        tool_calls=tool_calls,
        properties=properties,
    )


def stream_agent(session: Session, message: str, thread_id: str | None = None) -> Iterator[dict]:
    """Yield SSE-friendly event dicts as the agent runs."""
    thread_id = thread_id or str(uuid.uuid4())
    graph = get_agent_graph()
    properties: list[dict] = []
    seen: set[str] = set()

    for mode, data in graph.stream(
        {"messages": [HumanMessage(message)]},
        config=_config(thread_id, session),
        stream_mode=["messages", "updates"],
    ):
        if mode == "messages":
            chunk, _meta = data
            if isinstance(chunk, AIMessageChunk):
                text = _text(chunk.content)
                if text:
                    yield {"type": "token", "text": text}
            elif isinstance(chunk, ToolMessage):
                before = len(properties)
                _properties_from_tool_message(chunk, properties, seen)
                yield {
                    "type": "tool_result",
                    "name": chunk.name,
                    "new_properties": len(properties) - before,
                }
        elif mode == "updates" and "agent" in data:
            last = data["agent"]["messages"][-1]
            for call in getattr(last, "tool_calls", None) or []:
                yield {
                    "type": "tool_call",
                    "name": call["name"],
                    "args": call["args"],
                }

    yield {"type": "done", "thread_id": thread_id, "properties": properties}
