import json
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional, Protocol, Any

from fastapi import Depends
from redis.asyncio import Redis

from db import postgres
from db.redis import get_redis
from models.events import EventDetail, EventListItem, Tier, Venue

CACHE_TTL_SECONDS = 300


class CacheInterface(Protocol):
    async def get(self, key: str) -> Any:
        ...

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> Any:
        ...


class RedisCache(CacheInterface):
    def __init__(self, redis_client: Any):
        self.redis = redis_client

    async def get(self, key: str) -> Any:
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> Any:
        return await self.redis.set(key, value, ex=ex)


class EventRepositoryInterface(Protocol):
    async def get_events_count(self, query: str | None = None) -> int:
        ...

    async def get_events_page(
        self,
        page: int,
        page_size: int,
        query: str | None = None,
        sort: str | None = "date",
        request_time: datetime | None = None
    ) -> list[dict]:
        ...

    async def get_event_detail(self, event_id: str) -> Optional[dict]:
        ...

    async def get_event_tiers(self, event_id: str, request_time: datetime) -> list[dict]:
        ...


class PostgresEventRepository(EventRepositoryInterface):
    def __init__(self, pool: Any = None):
        self._pool = pool

    @property
    def pool(self) -> Any:
        if self._pool is not None:
            return self._pool
        return postgres.get_pool()

    async def get_events_count(self, query: str | None = None) -> int:
        async with self.pool.acquire() as conn:
            return await postgres.fetch_events_count(conn, query=query)

    async def get_events_page(
        self,
        page: int,
        page_size: int,
        query: str | None = None,
        sort: str | None = "date",
        request_time: datetime | None = None
    ) -> list[dict]:
        if request_time is None:
            request_time = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            records = await postgres.fetch_events_page(
                conn,
                page=page,
                page_size=page_size,
                query=query,
                sort=sort,
                request_time=request_time
            )
            return [dict(r) for r in records]

    async def get_event_detail(self, event_id: str) -> Optional[dict]:
        async with self.pool.acquire() as conn:
            record = await postgres.fetch_event_detail(conn, event_id)
            return dict(record) if record else None

    async def get_event_tiers(self, event_id: str, request_time: datetime) -> list[dict]:
        async with self.pool.acquire() as conn:
            records = await postgres.fetch_event_tiers(conn, event_id, request_time=request_time)
            return [dict(r) for r in records]


class EventSearchInterface(Protocol):
    async def search_events(
        self,
        query: str,
        page: int,
        page_size: int,
        sort: str | None = "date",
        request_time: datetime | None = None
    ) -> tuple[int, list[dict]]:
        ...


class PostgresEventSearch(EventSearchInterface):
    def __init__(self, repository: EventRepositoryInterface):
        self.repository = repository

    async def search_events(
        self,
        query: str,
        page: int,
        page_size: int,
        sort: str | None = "date",
        request_time: datetime | None = None
    ) -> tuple[int, list[dict]]:
        total = await self.repository.get_events_count(query=query)
        results = await self.repository.get_events_page(
            page=page,
            page_size=page_size,
            query=query,
            sort=sort,
            request_time=request_time
        )
        return total, results


class EventService:
    def __init__(
        self,
        repository_or_cache: Any,
        cache_client: Optional[CacheInterface] = None,
        search_service: Optional[EventSearchInterface] = None
    ):
        # Backward compatibility for legacy tests that called EventService(mock_redis)
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
                    min_price=row["min_price"],
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
        min_price = None
        total_available = 0
        for tier_row in tiers_rows:
            quantity = int(tier_row["total_quantity"])
            sold = int(tier_row["sold"])
            available = max(quantity - sold, 0)
            total_available += available
            price = tier_row["price"]
            if min_price is None or price < min_price:
                min_price = price
            tiers.append(Tier(name=tier_row["name"], price=price, available=available))

        event = EventDetail(
            id=str(row["id"]),
            title=row["title"],
            starts_at=row["starts_at"],
            venue=Venue(name=row["venue_name"], city=row["venue_city"]),
            description=row["description"],
            min_price=min_price,
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
