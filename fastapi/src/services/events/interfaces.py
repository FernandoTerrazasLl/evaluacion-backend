from datetime import datetime
from typing import Optional, Protocol, Any

class CacheInterface(Protocol):
    async def get(self, key: str) -> Any:
        ...

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> Any:
        ...


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
