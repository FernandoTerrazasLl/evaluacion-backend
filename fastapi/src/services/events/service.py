import json
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional, Any

from fastapi import Depends
from redis.asyncio import Redis

from db import postgres
from db.redis import get_redis
from models.events import EventDetail, EventListItem, Tier, Venue

from .interfaces import CacheInterface, EventRepositoryInterface, EventSearchInterface
from .cache import CACHE_TTL_SECONDS, RedisCache
from .repository import PostgresEventRepository
from .search import PostgresEventSearch


class EventService:
    def __init__(
        self,
        repository_or_cache: Any,
        cache_client: Optional[CacheInterface] = None,
        search_service: Optional[EventSearchInterface] = None
    ):
        if cache_client is None and search_service is None:
            self.cache = repository_or_cache
            try:
                pool = postgres.get_pool()
            except Exception:
                pool = None
            self.repository = PostgresEventRepository(pool)
            self.search_service = PostgresEventSearch(self.repository)
        else:
            self.repository = repository_or_cache
            self.cache = cache_client
            self.search_service = search_service

    async def list_events(
        self,
        page: int,
        page_size: int,
        query: str | None = None,
        sort: str | None = "date",
        request_time: Optional[datetime] = None
    ) -> tuple[int, list[EventListItem]]:
        if request_time is None:
            request_time = datetime.now(timezone.utc)

        rounded_ts = int(request_time.timestamp() / 10) * 10
        cache_key = f"events:list:{page}:{page_size}:{query or ''}:{sort or ''}:{rounded_ts}"
        
        cached = await self._get_cache(cache_key)
        if cached is not None:
            return cached["count"], [EventListItem.model_validate(item) for item in cached["results"]]

        if query:
            total, rows = await self.search_service.search_events(
                query=query,
                page=page,
                page_size=page_size,
                sort=sort,
                request_time=request_time
            )
        else:
            total = await self.repository.get_events_count()
            rows = await self.repository.get_events_page(
                page=page,
                page_size=page_size,
                sort=sort,
                request_time=request_time
            )

        items: list[EventListItem] = []
        for row in rows:
            total_quantity = int(row["total_quantity"])
            sold = int(row["sold"])
            available = max(total_quantity - sold, 0)
            
            items.append(
                EventListItem(
                    id=str(row["id"]),
                    title=row["title"],
                    starts_at=row["starts_at"],
                    venue=Venue(name=row["venue_name"], city=row["venue_city"]),
                    current_price=row["current_price"],
                    current_tier_id=str(row["current_tier_id"]),
                    available=available,
                    total_capacity=int(row["total_capacity"]),
                )
            )

        await self._set_cache(cache_key, {
            "count": total,
            "results": [item.model_dump() for item in items],
        })
        return total, items

    async def get_event(self, event_id: str, request_time: Optional[datetime] = None) -> Optional[EventDetail]:
        if request_time is None:
            request_time = datetime.now(timezone.utc)

        rounded_ts = int(request_time.timestamp() / 10) * 10
        cache_key = f"events:detail:{event_id}:{rounded_ts}"
        
        cached = await self._get_cache(cache_key)
        if cached is not None:
            return EventDetail.model_validate(cached)

        row = await self.repository.get_event_detail(event_id)
        if not row:
            return None
        tiers_rows = await self.repository.get_event_tiers(event_id, request_time=request_time)

        tiers: list[Tier] = []
        current_price = None
        total_available = 0
        current_tier_id="" #
        for tier_row in tiers_rows:
            quantity = int(tier_row["total_quantity"])
            sold = int(tier_row["sold"])
            available = max(quantity - sold, 0)
            total_available += available
            price = tier_row["price"]
            if current_price is None or price < current_price:
                current_price = price
                current_tier_id = str(tier_row["id"])#
            tiers.append(Tier(name=tier_row["name"], price=price, available=available))

        event = EventDetail(
            id=str(row["id"]),
            title=row["title"],
            starts_at=row["starts_at"],
            venue=Venue(name=row["venue_name"], city=row["venue_city"]),
            description=row["description"],
            current_price=current_price,
            current_tier_id=str(current_tier_id),
            available=total_available,
            total_capacity=int(row["total_capacity"]),
            tiers=tiers,
        )

        await self._set_cache(cache_key, event.model_dump())
        return event

    async def _get_cache(self, key: str) -> Optional[dict]:
        try:
            raw = await self.cache.get(key)
        except Exception:
            return None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    async def _set_cache(self, key: str, value: dict) -> None:
        try:
            await self.cache.set(key, json.dumps(value, default=str), ex=CACHE_TTL_SECONDS)
        except Exception:
            return None


@lru_cache()
def get_event_service(
    redis_client: Redis = Depends(get_redis),
    pool = Depends(postgres.get_pool)
) -> EventService:
    cache = RedisCache(redis_client)
    repository = PostgresEventRepository(pool)
    search_service = PostgresEventSearch(repository)
    return EventService(repository, cache, search_service)
