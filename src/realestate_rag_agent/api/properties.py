import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from realestate_rag_agent.api.schemas import (
    PropertyCreate,
    PropertyPage,
    PropertyRead,
    PropertyUpdate,
)
from realestate_rag_agent.core.db import get_session
from realestate_rag_agent.repositories.models import Operation, PropertyType
from realestate_rag_agent.repositories.property_repository import PropertyFilter
from realestate_rag_agent.services import property_service
from realestate_rag_agent.services.property_service import PropertyNotFoundError

router = APIRouter(prefix="/properties", tags=["properties"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=PropertyPage)
def list_properties(
    session: SessionDep,
    operation: Operation | None = None,
    property_type: PropertyType | None = None,
    city: str | None = None,
    neighborhood: str | None = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    min_bedrooms: Annotated[int | None, Query(ge=0)] = None,
    min_area: Annotated[float | None, Query(gt=0)] = None,
    amenities: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PropertyPage:
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
    items, total = property_service.list_properties(session, f, limit=limit, offset=offset)
    return PropertyPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: uuid.UUID, session: SessionDep) -> PropertyRead:
    try:
        return property_service.get_property(session, property_id)
    except PropertyNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(payload: PropertyCreate, session: SessionDep) -> PropertyRead:
    return property_service.create_property(session, payload)


@router.patch("/{property_id}", response_model=PropertyRead)
def update_property(
    property_id: uuid.UUID, payload: PropertyUpdate, session: SessionDep
) -> PropertyRead:
    try:
        return property_service.update_property(session, property_id, payload)
    except PropertyNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: uuid.UUID, session: SessionDep) -> Response:
    try:
        property_service.delete_property(session, property_id)
    except PropertyNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
