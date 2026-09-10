import json
from collections.abc import AsyncIterator
from typing import Annotated

import asyncpg
from fastapi import Depends, Request

from todo_api.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS board_columns (
    id text PRIMARY KEY,
    title text NOT NULL,
    position integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cards (
    id text PRIMARY KEY,
    column_id text NOT NULL REFERENCES board_columns(id) ON DELETE CASCADE,
    title text NOT NULL,
    position integer NOT NULL,
    body jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS cards_column_idx ON cards (column_id, position);

CREATE TABLE IF NOT EXISTS inbox_items (
    id text PRIMARY KEY,
    title text NOT NULL,
    position integer NOT NULL,
    body jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
"""


async def _init_connection(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def create_pool() -> asyncpg.Pool:
    pool = await asyncpg.create_pool(settings.database_url, init=_init_connection)
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)
    return pool


async def get_connection(request: Request) -> AsyncIterator[asyncpg.Connection]:
    async with request.app.state.pool.acquire() as conn:
        yield conn


ConnDep = Annotated[asyncpg.Connection, Depends(get_connection)]
