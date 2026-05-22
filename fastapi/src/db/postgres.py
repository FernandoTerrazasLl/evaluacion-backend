import os
import asyncio
import logging
from datetime import datetime
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)

pool: Optional[asyncpg.Pool] = None

async def init_db_pool() -> None:
    global pool
    postgres_sql = os.getenv("POSTGRES_DSN") or os.getenv("POSTGRES_URL")
    if not postgres_sql:
        raise RuntimeError(
            "Postgres DSN not configured. Set POSTGRES_DSN or POSTGRES_URL to a valid connection string. "
            "Example: postgresql://user:password@postgres:5432/mydb"
        )
    
    max_retries = 15
    retry_delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            pool = await asyncpg.create_pool(postgres_sql)
            logger.info("Successfully connected to PostgreSQL database")
            break
        except (OSError, asyncpg.PostgresError) as e:
            if attempt == max_retries:
                logger.error("Failed to connect to PostgreSQL database after %d attempts: %s", max_retries, e)
                raise
            logger.warning("PostgreSQL not ready (attempt %d/%d): %s. Retrying in %d seconds...", attempt, max_retries, e, retry_delay)
            await asyncio.sleep(retry_delay)


async def close_db_pool() -> None:
    global pool
    if pool:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    if not pool:
        raise RuntimeError("Postgres pool is not initialized")
    return pool


async def fetch_events_count(conn: asyncpg.Connection, query: str | None = None) -> int:
    if query:
        sql = """
            SELECT COUNT(*)
            FROM content.event e
            JOIN content.venue v ON v.id = e.venue_id
            WHERE e.title ILIKE $1 OR e.description ILIKE $1 OR v.name ILIKE $1 OR v.city ILIKE $1
        """
        return await conn.fetchval(sql, f"%{query}%")
    sql = "SELECT COUNT(*) FROM content.event"
    return await conn.fetchval(sql)


async def fetch_events_page(
    conn: asyncpg.Connection,
    *,
    page: int,
    page_size: int,
    query: str | None = None,
    sort: str | None = "date",
    request_time: datetime
) -> list[asyncpg.Record]:
    offset = (page - 1) * page_size
    #CAMBIO DEL EXAMEN
    base_sql = """
        SELECT
            e.id,
            e.title,
            e.starts_at,
            e.total_capacity,
            v.name AS venue_name,
            v.city AS venue_city,
            (
                SELECT MIN(price)
                FROM content.tickettype
                WHERE event_id = e.id
                  AND (start_date IS NULL OR $1::timestamp with time zone >= start_date)
                  AND (end_date IS NULL OR $1::timestamp with time zone <= end_date)
            ) AS current_price,
            (
                SELECT id 
                FROM content.tickettype 
                where event_id=e.id
                order by price
                limit 1
            ) AS current_tier_id,
            (SELECT COALESCE(SUM(total_quantity), 0) FROM content.tickettype WHERE event_id = e.id) AS total_quantity,
            (SELECT COUNT(*) FROM content.ticket t JOIN content.tickettype tt ON t.ticket_type_id = tt.id WHERE tt.event_id = e.id) AS sold
        FROM content.event e
        JOIN content.venue v ON v.id = e.venue_id
    """
    
    where_clause = ""
    params = [request_time]
    
    if query:
        where_clause = " WHERE e.title ILIKE $2 OR e.description ILIKE $2 OR v.name ILIKE $2 OR v.city ILIKE $2"
        params.append(f"%{query}%")
    
    order_clause = " ORDER BY e.starts_at ASC"  
    if sort == "price":
        order_clause = " ORDER BY min_price ASC NULLS LAST"
    elif sort == "capacity":
        order_clause = " ORDER BY ((SELECT COALESCE(SUM(total_quantity), 0) FROM content.tickettype WHERE event_id = e.id) - (SELECT COUNT(*) FROM content.ticket t JOIN content.tickettype tt ON t.ticket_type_id = tt.id WHERE tt.event_id = e.id)) DESC"
        
    sql = base_sql + where_clause + order_clause + f" LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([page_size, offset])
    
    return await conn.fetch(sql, *params)


async def fetch_event_detail(conn: asyncpg.Connection, event_id: str) -> asyncpg.Record | None:
    sql = """
        SELECT
            e.id,
            e.title,
            e.description,
            e.starts_at,
            e.total_capacity,
            v.name AS venue_name,
            v.city AS venue_city
        FROM content.event e
        JOIN content.venue v ON v.id = e.venue_id
        WHERE e.id = $1
    """
    return await conn.fetchrow(sql, event_id)


async def fetch_event_tiers(conn: asyncpg.Connection, event_id: str, request_time: datetime) -> list[asyncpg.Record]:
    sql = """
        SELECT
            tt.id,
            tt.name,
            tt.price,
            tt.total_quantity,
            COALESCE(COUNT(t.id), 0) AS sold
        FROM content.tickettype tt
        LEFT JOIN content.ticket t ON t.ticket_type_id = tt.id
        WHERE tt.event_id = $1
          AND (tt.start_date IS NULL OR $2::timestamp with time zone >= tt.start_date)
          AND (tt.end_date IS NULL OR $2::timestamp with time zone <= tt.end_date)
        GROUP BY tt.id, tt.name, tt.price, tt.total_quantity
        ORDER BY tt.price
    """
    return await conn.fetch(sql, event_id, request_time)