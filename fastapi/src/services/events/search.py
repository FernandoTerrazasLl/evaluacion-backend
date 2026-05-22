from datetime import datetime
from .interfaces import EventRepositoryInterface, EventSearchInterface


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
