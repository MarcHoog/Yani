import json
from collections.abc import AsyncIterator
from typing import Annotated

import asyncpg
from fastapi import Depends, Request

from todo_api.config import settings

# customer_id is added with ALTER as well so an old dev volume fails loudly at startup when it
# holds rows without one (reset it with `python dev.py down -v`), instead of failing per query.
SCHEMA = """
CREATE TABLE IF NOT EXISTS board_columns (
    id text PRIMARY KEY,
    customer_id text NOT NULL,
    title text NOT NULL,
    position integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cards (
    id text PRIMARY KEY,
    customer_id text NOT NULL,
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
    customer_id text NOT NULL,
    title text NOT NULL,
    position integer NOT NULL,
    body jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE board_columns ADD COLUMN IF NOT EXISTS customer_id text NOT NULL;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS customer_id text NOT NULL;
ALTER TABLE inbox_items ADD COLUMN IF NOT EXISTS customer_id text NOT NULL;

-- A card belongs to the same customer as its column, enforced by the database too.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'board_columns_id_customer_key') THEN
        ALTER TABLE board_columns
            ADD CONSTRAINT board_columns_id_customer_key UNIQUE (id, customer_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cards_column_customer_fkey') THEN
        ALTER TABLE cards
            ADD CONSTRAINT cards_column_customer_fkey FOREIGN KEY (column_id, customer_id)
            REFERENCES board_columns (id, customer_id) ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS board_columns_customer_idx ON board_columns (customer_id, position);
CREATE INDEX IF NOT EXISTS cards_customer_idx ON cards (customer_id);
CREATE INDEX IF NOT EXISTS inbox_items_customer_idx ON inbox_items (customer_id, position);
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
