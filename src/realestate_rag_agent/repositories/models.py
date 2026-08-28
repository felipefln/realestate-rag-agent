import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from realestate_rag_agent.core.db import Base

EMBEDDING_DIM = 1536


class Operation(enum.StrEnum):
    sale = "sale"
    rent = "rent"


class PropertyType(enum.StrEnum):
    apartment = "apartment"
    house = "house"
    studio = "studio"
    condo = "condo"
    land = "land"
    commercial = "commercial"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    operation: Mapped[Operation] = mapped_column(Enum(Operation, name="operation"))
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType, name="property_type"))

    price: Mapped[float] = mapped_column(Numeric(12, 2))
    condo_fee: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    iptu: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    bedrooms: Mapped[int] = mapped_column(default=0)
    bathrooms: Mapped[int] = mapped_column(default=0)
    parking_spaces: Mapped[int] = mapped_column(default=0)
    area_m2: Mapped[float] = mapped_column(Numeric(10, 2))

    neighborhood: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(120), default="Florianópolis")
    state: Mapped[str] = mapped_column(String(2), default="SC")
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)

    amenities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, server_default="{}")

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_properties_price_non_negative"),
        CheckConstraint("area_m2 > 0", name="ck_properties_area_positive"),
        Index("ix_properties_operation", "operation"),
        Index("ix_properties_city", "city"),
        Index("ix_properties_neighborhood", "neighborhood"),
        Index("ix_properties_price", "price"),
    )
