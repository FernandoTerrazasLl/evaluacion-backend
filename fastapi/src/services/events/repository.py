from datetime import datetime, timezone
from typing import Optional, Any

from db import postgres
from .interfaces import EventRepositoryInterface


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
