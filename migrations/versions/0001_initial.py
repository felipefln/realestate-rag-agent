"""initial properties table

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-27

"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

operation_enum = sa.Enum("sale", "rent", name="operation")
property_type_enum = sa.Enum(
    "apartment", "house", "studio", "condo", "land", "commercial", name="property_type"
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "properties",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("operation", operation_enum, nullable=False),
        sa.Column("property_type", property_type_enum, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("condo_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("iptu", sa.Numeric(12, 2), nullable=True),
        sa.Column("bedrooms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bathrooms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parking_spaces", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("area_m2", sa.Numeric(10, 2), nullable=False),
        sa.Column("neighborhood", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column(
            "amenities",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("price >= 0", name="ck_properties_price_non_negative"),
        sa.CheckConstraint("area_m2 > 0", name="ck_properties_area_positive"),
    )
    op.create_index("ix_properties_operation", "properties", ["operation"])
    op.create_index("ix_properties_city", "properties", ["city"])
    op.create_index("ix_properties_neighborhood", "properties", ["neighborhood"])
    op.create_index("ix_properties_price", "properties", ["price"])


def downgrade() -> None:
    op.drop_index("ix_properties_price", table_name="properties")
    op.drop_index("ix_properties_neighborhood", table_name="properties")
    op.drop_index("ix_properties_city", table_name="properties")
    op.drop_index("ix_properties_operation", table_name="properties")
    op.drop_table("properties")
    property_type_enum.drop(op.get_bind(), checkfirst=True)
    operation_enum.drop(op.get_bind(), checkfirst=True)
