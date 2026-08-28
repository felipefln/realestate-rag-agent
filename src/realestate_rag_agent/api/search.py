from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from realestate_rag_agent.api.schemas import SearchHitRead, SearchResponse
from realestate_rag_agent.core.db import get_session
from realestate_rag_agent.repositories.models import Operation, PropertyType
from realestate_rag_agent.repositories.property_repository import PropertyFilter
from realestate_rag_agent.services import search_service

router = APIRouter(tags=["search"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/search", response_model=SearchResponse)
def search(
    session: SessionDep,
    q: Annotated[str, Query(min_length=2, description="natural language query")],
    operation: Operation | None = None,
    property_type: PropertyType | None = None,
    city: str | None = None,
    neighborhood: str | None = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    min_bedrooms: Annotated[int | None, Query(ge=0)] = None,
    min_area: Annotated[float | None, Query(gt=0)] = None,
    amenities: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> SearchResponse:
    f = PropertyFilter(
        operation=operation,
        property_type=property_type,
        city=city,
        neighborhood=neighborhood,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        min_area=min_area,
        amenities=amenities,
    )
    hits = search_service.search(session, q, f, limit=limit)
    return SearchResponse(
        query=q,
        count=len(hits),
        items=[SearchHitRead(score=h.score, property=h.property) for h in hits],
    )
