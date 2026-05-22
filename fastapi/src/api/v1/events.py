from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.v1.models.event import EventDetailOut, EventListItemOut, PaginatedEventsOut, PriceHistoryOut, HistoryOut
from core import config
from core.limiter import limiter, get_rate_limit
from services.events import EventService, get_event_service

router = APIRouter()

@router.get('/', response_model=PaginatedEventsOut)
@limiter.limit(get_rate_limit)
async def list_events(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    sort: str | None = Query("date"),
    request_time: datetime | None = Query(None),
    event_service: EventService = Depends(get_event_service),
) -> PaginatedEventsOut:
    count, results = await event_service.list_events(page=page, page_size=page_size, query=q, sort=sort, request_time=request_time)
    return PaginatedEventsOut(
        count=count,
        page=page,
        results=[EventListItemOut.model_validate(item.model_dump()) for item in results],
    )

@router.get('/search/', response_model=PaginatedEventsOut)
@limiter.limit(get_rate_limit)
async def search_events(
    request: Request,
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str | None = Query("date"),
    request_time: datetime | None = Query(None),
    event_service: EventService = Depends(get_event_service),
) -> PaginatedEventsOut:
    count, results = await event_service.list_events(page=page, page_size=page_size, query=query, sort=sort, request_time=request_time)
    return PaginatedEventsOut(
        count=count,
        page=page,
        results=[EventListItemOut.model_validate(item.model_dump()) for item in results],
    )

@router.get('/{event_id}', response_model=EventDetailOut)
@limiter.limit(get_rate_limit)
async def event_details(
    request: Request,
    event_id: str,
    request_time: datetime | None = Query(None),
    event_service: EventService = Depends(get_event_service),
) -> EventDetailOut:
    event = await event_service.get_event(event_id, request_time=request_time)
    if not event:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='event not found')
    return EventDetailOut.model_validate(event.model_dump())

@router.get('/{id}/price-history')
@limiter.limit(get_rate_limit)
async def list_events(
    request: Request,
    id: str,
    event_service: EventService = Depends(get_event_service),
) -> PriceHistoryOut:
    lista = await event_service.get_event_price_history(id)
    return PriceHistoryOut(
        diccionario=[HistoryOut.model_validate(item.model_dump()) for item in lista]
    )