import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from realestate_rag_agent.repositories.models import Operation, PropertyType


class PropertyBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    operation: Operation
    property_type: PropertyType
    price: float = Field(ge=0)
    condo_fee: float | None = Field(default=None, ge=0)
    iptu: float | None = Field(default=None, ge=0)
    bedrooms: int = Field(default=0, ge=0)
    bathrooms: int = Field(default=0, ge=0)
    parking_spaces: int = Field(default=0, ge=0)
    area_m2: float = Field(gt=0)
    neighborhood: str = Field(min_length=2, max_length=120)
    city: str = "Florianópolis"
    state: str = Field(default="SC", min_length=2, max_length=2)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    amenities: list[str] = Field(default_factory=list)


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=10)
    operation: Operation | None = None
    property_type: PropertyType | None = None
    price: float | None = Field(default=None, ge=0)
    condo_fee: float | None = Field(default=None, ge=0)
    iptu: float | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    parking_spaces: int | None = Field(default=None, ge=0)
    area_m2: float | None = Field(default=None, gt=0)
    neighborhood: str | None = Field(default=None, min_length=2, max_length=120)
    city: str | None = None
    state: str | None = Field(default=None, min_length=2, max_length=2)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    amenities: list[str] | None = None


class PropertyRead(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PropertyPage(BaseModel):
    items: list[PropertyRead]
    total: int
    limit: int
    offset: int


class SearchHitRead(BaseModel):
    score: float
    property: PropertyRead


class SearchResponse(BaseModel):
    query: str
    count: int
    items: list[SearchHitRead]


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    thread_id: str | None = None


class AgentToolCall(BaseModel):
    name: str
    args: dict


class AgentChatResponse(BaseModel):
    thread_id: str
    reply: str
    tool_calls: list[AgentToolCall]
    properties: list[dict]
