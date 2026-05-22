from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Venue(BaseModel):
    name: str
    city: str


class Tier(BaseModel):
    name: str
    price: Decimal
    available: int


class EventListItem(BaseModel):
    id: str
    title: str
    starts_at: datetime
    venue: Venue
    min_price: Decimal | None
    available: int
    total_capacity: int


class EventDetail(BaseModel):
    id: str
    title: str
    starts_at: datetime
    venue: Venue
    description: str | None
    min_price: Decimal | None
    available: int
    total_capacity: int
    tiers: list[Tier]