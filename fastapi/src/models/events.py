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
    current_price: Decimal | None
    current_tier_id: str
    available: int
    total_capacity: int


class EventDetail(BaseModel):
    id: str
    title: str
    starts_at: datetime
    venue: Venue
    description: str | None
    current_price: Decimal | None
    current_tier_id: str
    available: int
    total_capacity: int
    tiers: list[Tier]

class PriceHistory(BaseModel):
    price: Decimal
    date: datetime