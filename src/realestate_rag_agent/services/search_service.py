from dataclasses import dataclass

from sqlalchemy.orm import Session

from realestate_rag_agent.repositories import property_repository as repo
from realestate_rag_agent.repositories.models import Property
from realestate_rag_agent.repositories.property_repository import PropertyFilter
from realestate_rag_agent.services.embeddings import embedding_text, get_embedder


@dataclass
class SearchHit:
    property: Property
    score: float


def search(session: Session, query: str, f: PropertyFilter, *, limit: int = 10) -> list[SearchHit]:
    query_vec = get_embedder().embed_one(query)
    rows = repo.search_by_vector(session, query_vec, f, limit=limit)
    return [SearchHit(property=prop, score=score) for prop, score in rows]


def compute_embedding(title: str, description: str) -> list[float]:
    return get_embedder().embed_one(embedding_text(title, description))
