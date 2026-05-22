from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class VenueOut(BaseModel):
    name: str
    city: str


class TierOut(BaseModel):
    name: str
    price: Decimal
    available: int


class EventListItemOut(BaseModel):
    id: str
    title: str
    starts_at: datetime
    venue: VenueOut
    current_price: Decimal | None
    current_tier_id: str
    available: int
    total_capacity: int


class EventDetailOut(BaseModel):
    id: str
    title: str
    starts_at: datetime
    venue: VenueOut
    description: str | None
    current_price: Decimal | None
    available: int
    total_capacity: int
    tiers: list[TierOut]


class PaginatedEventsOut(BaseModel):
    count: int
    page: int
    results: list[EventListItemOut]

class PriceHistoryOut(BaseModel):
    diccionario: dict

class HistoryOut(BaseModel):
    price: Decimal | None
    date: datetime
