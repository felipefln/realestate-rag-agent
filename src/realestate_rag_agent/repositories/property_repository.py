import uuid

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from realestate_rag_agent.repositories.models import Operation, Property, PropertyType


class PropertyFilter(BaseModel):
    operation: Operation | None = None
    property_type: PropertyType | None = None
    city: str | None = None
    neighborhood: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    min_bedrooms: int | None = None
    min_area: float | None = None
    amenities: list[str] | None = None


def _apply_filter(stmt, f: PropertyFilter):
    if f.operation is not None:
        stmt = stmt.where(Property.operation == f.operation)
    if f.property_type is not None:
        stmt = stmt.where(Property.property_type == f.property_type)
    if f.city is not None:
        stmt = stmt.where(Property.city.ilike(f.city))
    if f.neighborhood is not None:
        stmt = stmt.where(Property.neighborhood.ilike(f.neighborhood))
    if f.min_price is not None:
        stmt = stmt.where(Property.price >= f.min_price)
    if f.max_price is not None:
        stmt = stmt.where(Property.price <= f.max_price)
    if f.min_bedrooms is not None:
        stmt = stmt.where(Property.bedrooms >= f.min_bedrooms)
    if f.min_area is not None:
        stmt = stmt.where(Property.area_m2 >= f.min_area)
    if f.amenities:
        stmt = stmt.where(Property.amenities.contains(f.amenities))
    return stmt


def get(session: Session, property_id: uuid.UUID) -> Property | None:
    return session.get(Property, property_id)


def list_properties(
    session: Session,
    f: PropertyFilter,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Property], int]:
    base = _apply_filter(select(Property), f)

    total = session.scalar(_apply_filter(select(func.count()).select_from(Property), f))

    rows = session.scalars(
        base.order_by(Property.created_at.desc()).limit(limit).offset(offset)
    ).all()

    return list(rows), int(total or 0)


def create(session: Session, data: dict) -> Property:
    prop = Property(**data)
    session.add(prop)
    session.commit()
    session.refresh(prop)
    return prop


def update(session: Session, prop: Property, data: dict) -> Property:
    for key, value in data.items():
        setattr(prop, key, value)
    session.commit()
    session.refresh(prop)
    return prop


def delete(session: Session, prop: Property) -> None:
    session.delete(prop)
    session.commit()
