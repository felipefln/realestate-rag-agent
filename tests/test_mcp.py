"""The MCP server exposes the same searches as tools over stdio.

These tests call the tools in-process (no stdio transport) against the test DB.
"""

import json

import pytest
from sqlalchemy.orm import Session

from realestate_rag_agent.repositories.models import Property
from realestate_rag_agent.services.search_service import compute_embedding


@pytest.fixture
def seeded(db_session: Session) -> Session:
    for i in range(3):
        prop = Property(
            title=f"Apartamento {i} na Trindade",
            description="Apartamento perto da UFSC, ótimo para estudantes.",
            operation="rent",
            property_type="apartment",
            price=2500 + i,
            area_m2=55,
            neighborhood="Trindade",
            city="Florianópolis",
            state="SC",
        )
        prop.embedding = compute_embedding(prop.title, prop.description)
        db_session.add(prop)
    db_session.commit()
    return db_session


async def test_mcp_lists_tools() -> None:
    from realestate_rag_agent.mcp_server import mcp

    names = {t.name for t in await mcp.list_tools()}
    assert names == {"search_properties", "filter_properties", "get_property_details"}


def test_mcp_search_tool_runs(seeded: Session, monkeypatch) -> None:
    from realestate_rag_agent import mcp_server

    monkeypatch.setattr(mcp_server, "SessionLocal", lambda: _NoCloseSession(seeded))

    raw = mcp_server.search_properties(query="apartamento perto da UFSC", limit=5)
    results = json.loads(raw)
    assert results
    assert all(r["neighborhood"] == "Trindade" for r in results)


class _NoCloseSession:
    """Wrap the test session so `with SessionLocal() as s` doesn't close it."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def __enter__(self) -> Session:
        return self._session

    def __exit__(self, *exc) -> None:
        pass
