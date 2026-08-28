"""Generate embeddings for properties and store them in the `embedding` column.

Uses the provider selected by APP_EMBEDDING_PROVIDER (default: local
sentence-transformers). Only rows without an embedding are processed unless --all.

Usage:
    uv run python -m scripts.embed_properties
    uv run python -m scripts.embed_properties --all
    uv run python -m scripts.embed_properties --batch-size 64
"""

import argparse

from sqlalchemy import select

from realestate_rag_agent.core.db import SessionLocal
from realestate_rag_agent.repositories.models import Property
from realestate_rag_agent.services.embeddings import embedding_text, get_embedder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="recompute every property")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    embedder = get_embedder()
    with SessionLocal() as session:
        stmt = select(Property).order_by(Property.created_at)
        if not args.all:
            stmt = stmt.where(Property.embedding.is_(None))
        rows = list(session.scalars(stmt))

        if not rows:
            print("nothing to embed")
            return

        print(
            f"embedding {len(rows)} properties with {embedder.__class__.__name__} "
            f"({embedder.dim} dims)"
        )
        for start in range(0, len(rows), args.batch_size):
            batch = rows[start : start + args.batch_size]
            vectors = embedder.embed([embedding_text(p.title, p.description) for p in batch])
            for prop, vec in zip(batch, vectors, strict=True):
                prop.embedding = vec
            session.commit()
            print(f"  {min(start + args.batch_size, len(rows))}/{len(rows)}")

    print("done")


if __name__ == "__main__":
    main()
