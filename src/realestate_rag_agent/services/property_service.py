import uuid

from sqlalchemy.orm import Session

from realestate_rag_agent.api.schemas import PropertyCreate, PropertyUpdate
from realestate_rag_agent.repositories import property_repository as repo
from realestate_rag_agent.repositories.models import Property
from realestate_rag_agent.repositories.property_repository import PropertyFilter
from realestate_rag_agent.services.search_service import compute_embedding


class PropertyNotFoundError(Exception):
    def __init__(self, property_id: uuid.UUID) -> None:
        super().__init__(f"Property {property_id} not found")
        self.property_id = property_id


def get_property(session: Session, property_id: uuid.UUID) -> Property:
    prop = repo.get(session, property_id)
    if prop is None:
        raise PropertyNotFoundError(property_id)
    return prop


def list_properties(
    session: Session, f: PropertyFilter, *, limit: int, offset: int
) -> tuple[list[Property], int]:
    return repo.list_properties(session, f, limit=limit, offset=offset)


def create_property(session: Session, payload: PropertyCreate) -> Property:
    data = payload.model_dump()
    data["embedding"] = compute_embedding(data["title"], data["description"])
    return repo.create(session, data)


def update_property(session: Session, property_id: uuid.UUID, payload: PropertyUpdate) -> Property:
    prop = get_property(session, property_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return prop
    if "title" in changes or "description" in changes:
        changes["embedding"] = compute_embedding(
            changes.get("title", prop.title),
            changes.get("description", prop.description),
        )
    return repo.update(session, prop, changes)


def delete_property(session: Session, property_id: uuid.UUID) -> None:
    prop = get_property(session, property_id)
    repo.delete(session, prop)
