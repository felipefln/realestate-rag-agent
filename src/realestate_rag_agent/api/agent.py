import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from realestate_rag_agent.agent import service as agent_service
from realestate_rag_agent.api.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentToolCall,
)
from realestate_rag_agent.core.db import get_session

router = APIRouter(prefix="/agent", tags=["agent"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/chat", response_model=AgentChatResponse)
def chat(payload: AgentChatRequest, session: SessionDep) -> AgentChatResponse:
    try:
        result = agent_service.run_agent(session, payload.message, payload.thread_id)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return AgentChatResponse(
        thread_id=result.thread_id,
        reply=result.reply,
        tool_calls=[AgentToolCall(name=c.name, args=c.args) for c in result.tool_calls],
        properties=result.properties,
    )


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
def chat_stream(payload: AgentChatRequest, session: SessionDep) -> StreamingResponse:
    def events():
        try:
            for event in agent_service.stream_agent(session, payload.message, payload.thread_id):
                yield _sse(event)
        except RuntimeError as exc:
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(events(), media_type="text/event-stream")
