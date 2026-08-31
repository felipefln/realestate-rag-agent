"""LangChain tools the agent can call.

Each tool runs a query against the property database. The DB session is passed
through the ``RunnableConfig`` (``configurable.db_session``) that LangGraph
threads into every tool call, so the caller controls the session lifecycle and
nothing relies on global/contextvar state.
"""

import json
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from realestate_rag_agent.repositories.models import Property
from realestate_rag_agent.repositories.property_repository import PropertyFilter
from realestate_rag_agent.services import property_service, search_service
from realestate_rag_agent.services.property_service import PropertyNotFoundError

SESSION_CONFIG_KEY = "db_session"


def _session(config: RunnableConfig) -> Session:
    session = (config or {}).get("configurable", {}).get(SESSION_CONFIG_KEY)
    if session is None:
        raise RuntimeError("no DB session in the tool config")
    return session


def _summary(prop: Property, score: float | None = None) -> dict:
    data = {
        "id": str(prop.id),
        "title": prop.title,
        "operation": prop.operation.value,
        "property_type": prop.property_type.value,
        "price": float(prop.price),
        "bedrooms": prop.bedrooms,
        "area_m2": float(prop.area_m2),
        "neighborhood": prop.neighborhood,
        "city": prop.city,
        "amenities": list(prop.amenities or []),
    }
    if score is not None:
        data["score"] = round(score, 4)
    return data


def _filter(
    operation: str | None,
    property_type: str | None,
    neighborhood: str | None,
    min_price: float | None,
    max_price: float | None,
    min_bedrooms: int | None,
    min_area: float | None,
    amenities: list[str] | None,
) -> PropertyFilter:
    return PropertyFilter(
        operation=operation,
        property_type=property_type,
        neighborhood=neighborhood,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        min_area=min_area,
        amenities=amenities,
    )


@tool(parse_docstring=True)
def search_properties(
    query: str,
    operation: str | None = None,
    property_type: str | None = None,
    neighborhood: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_bedrooms: int | None = None,
    min_area: float | None = None,
    amenities: list[str] | None = None,
    limit: int = 8,
    config: RunnableConfig = None,
) -> str:
    """Semantic search over property listings, optionally narrowed by filters.

    Use this when the user describes what they want in natural language
    ("apartamento aconchegante perto da praia").

    Args:
        query: Natural language description of the desired property.
        operation: "sale" or "rent".
        property_type: apartment, house, studio, condo, land or commercial.
        neighborhood: Neighborhood name (case-insensitive, exact match).
        min_price: Minimum price (sale value or monthly rent).
        max_price: Maximum price.
        min_bedrooms: Minimum number of bedrooms.
        min_area: Minimum private area in m².
        amenities: Amenities that must all be present (e.g. ["piscina"]).
        limit: Maximum number of results (1-20).
    """
    hits = search_service.search(
        _session(config),
        query,
        _filter(
            operation,
            property_type,
            neighborhood,
            min_price,
            max_price,
            min_bedrooms,
            min_area,
            amenities,
        ),
        limit=max(1, min(limit, 20)),
    )
    return json.dumps([_summary(h.property, h.score) for h in hits], ensure_ascii=False)


@tool(parse_docstring=True)
def filter_properties(
    operation: str | None = None,
    property_type: str | None = None,
    neighborhood: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_bedrooms: int | None = None,
    min_area: float | None = None,
    amenities: list[str] | None = None,
    limit: int = 8,
    config: RunnableConfig = None,
) -> str:
    """List properties by structured filters only (no semantic ranking).

    Use this for purely factual queries ("casas para alugar no Centro com 3
    quartos").

    Args:
        operation: "sale" or "rent".
        property_type: apartment, house, studio, condo, land or commercial.
        neighborhood: Neighborhood name (case-insensitive, exact match).
        min_price: Minimum price.
        max_price: Maximum price.
        min_bedrooms: Minimum number of bedrooms.
        min_area: Minimum private area in m².
        amenities: Amenities that must all be present.
        limit: Maximum number of results (1-20).
    """
    items, total = property_service.list_properties(
        _session(config),
        _filter(
            operation,
            property_type,
            neighborhood,
            min_price,
            max_price,
            min_bedrooms,
            min_area,
            amenities,
        ),
        limit=max(1, min(limit, 20)),
        offset=0,
    )
    return json.dumps({"total": total, "items": [_summary(p) for p in items]}, ensure_ascii=False)


@tool(parse_docstring=True)
def get_property_details(property_id: str, config: RunnableConfig = None) -> str:
    """Full details of a single property by its id.

    Args:
        property_id: The property UUID.
    """
    try:
        prop = property_service.get_property(_session(config), uuid.UUID(property_id))
    except (ValueError, PropertyNotFoundError):
        return json.dumps({"error": "property not found"})

    data = _summary(prop)
    data.update(
        description=prop.description,
        bathrooms=prop.bathrooms,
        parking_spaces=prop.parking_spaces,
        condo_fee=float(prop.condo_fee) if prop.condo_fee is not None else None,
        iptu=float(prop.iptu) if prop.iptu is not None else None,
        state=prop.state,
        latitude=prop.latitude,
        longitude=prop.longitude,
    )
    return json.dumps(data, ensure_ascii=False)


AGENT_TOOLS = [search_properties, filter_properties, get_property_details]
