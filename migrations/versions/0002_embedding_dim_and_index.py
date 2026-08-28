"""set embedding dimension to 384 and add HNSW index

Revision ID: 0002_embedding_index
Revises: 0001_initial
Create Date: 2026-08-28

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_embedding_index"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # No embeddings have been generated yet; safe to reset the column type.
    op.execute("ALTER TABLE properties ALTER COLUMN embedding TYPE vector(384) USING NULL")
    op.execute(
        "CREATE INDEX ix_properties_embedding ON properties "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_embedding")
    op.execute("ALTER TABLE properties ALTER COLUMN embedding TYPE vector(1536) USING NULL")
