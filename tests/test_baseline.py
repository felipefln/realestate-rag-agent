"""Baseline de qualidade da busca semântica.

Roda com o modelo de embeddings real (sentence-transformers), por isso é lento e
marcado `slow`. Localmente: `uv run pytest -m "not slow"` para pular.
"""

import json
from pathlib import Path

import pytest
import yaml
from sqlalchemy.orm import Session

from realestate_rag_agent.repositories import property_repository as repo
from realestate_rag_agent.repositories.models import Property
from realestate_rag_agent.repositories.property_repository import PropertyFilter
from realestate_rag_agent.services.embeddings import (
    SentenceTransformerEmbedder,
    embedding_text,
)

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "properties.json"
CASES = yaml.safe_load((Path(__file__).parent / "baseline" / "queries.yaml").read_text())

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@pytest.fixture(scope="module")
def embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(MODEL_NAME)


@pytest.fixture(scope="module")
def indexed_db(engine, embedder: SentenceTransformerEmbedder):
    records = json.loads(DATASET.read_text())
    with Session(engine) as session:
        session.query(Property).delete()
        texts = [embedding_text(r["title"], r["description"]) for r in records]
        vectors = embedder.embed(texts)
        for rec, vec in zip(records, vectors, strict=True):
            payload = {k: v for k, v in rec.items() if k != "street"}
            session.add(Property(**payload, embedding=vec))
        session.commit()
        yield session
        session.query(Property).delete()
        session.commit()


def _check(expect: dict, hits: list[Property]) -> list[str]:
    errors: list[str] = []

    if "all_property_type" in expect:
        want = expect["all_property_type"]
        bad = [h.property_type for h in hits if h.property_type != want]
        if bad:
            errors.append(f"esperava todos '{want}' no top-{len(hits)}, veio {bad}")

    if "min_property_type" in expect:
        want = expect["min_property_type"]["type"]
        need = expect["min_property_type"]["count"]
        got = sum(1 for h in hits if h.property_type == want)
        if got < need:
            errors.append(f"esperava >= {need} '{want}' no top-{len(hits)}, veio {got}")

    if "neighborhood_in_top" in expect:
        want = expect["neighborhood_in_top"]
        if want not in {h.neighborhood for h in hits}:
            errors.append(
                f"esperava bairro '{want}' no top-{len(hits)}, "
                f"veio {[h.neighborhood for h in hits]}"
            )

    if "min_amenity" in expect:
        want = expect["min_amenity"]["amenity"]
        need = expect["min_amenity"]["count"]
        got = sum(1 for h in hits if want in (h.amenities or []))
        if got < need:
            errors.append(f"esperava >= {need} com '{want}' no top-{len(hits)}, veio {got}")

    return errors


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_search_baseline(
    case: dict, indexed_db: Session, embedder: SentenceTransformerEmbedder
) -> None:
    query_vec = embedder.embed_one(case["query"])
    rows = repo.search_by_vector(indexed_db, query_vec, PropertyFilter(), limit=case["top_k"])
    hits = [prop for prop, _score in rows]

    assert len(hits) == case["top_k"]
    errors = _check(case["expect"], hits)
    assert not errors, f"{case['name']!r}: " + "; ".join(errors)
