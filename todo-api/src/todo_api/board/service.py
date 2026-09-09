from typing import Any

import asyncpg
from ulid import ULID

from todo_api.exceptions import NotFound

_COLUMN = "id, title, position, created_at, updated_at"
_CARD = "id, column_id, title, position, body, created_at, updated_at"

DEFAULT_COLUMNS = ["Backlog", "Doing", "Waiting", "Done"]


async def seed_columns(conn: asyncpg.Connection) -> None:
    if await conn.fetchval("SELECT count(*) FROM board_columns"):
        return
    for position, title in enumerate(DEFAULT_COLUMNS):
        await conn.execute(
            "INSERT INTO board_columns (id, title, position) VALUES ($1, $2, $3)",
            str(ULID()),
            title,
            position,
        )


async def get_board(conn: asyncpg.Connection) -> dict[str, Any]:
    columns = await conn.fetch(f"SELECT {_COLUMN} FROM board_columns ORDER BY position, id")
    cards = await conn.fetch(f"SELECT {_CARD} FROM cards ORDER BY position, id")
    by_column: dict[str, list[dict[str, Any]]] = {column["id"]: [] for column in columns}
    for card in cards:
        by_column[card["column_id"]].append(dict(card))
    return {"columns": [dict(column) | {"cards": by_column[column["id"]]} for column in columns]}


async def create_column(conn: asyncpg.Connection, title: str) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        INSERT INTO board_columns (id, title, position)
        VALUES ($1, $2, (SELECT coalesce(max(position) + 1, 0) FROM board_columns))
        RETURNING {_COLUMN}
        """,
        str(ULID()),
        title,
    )
    return dict(row)


async def update_column(
    conn: asyncpg.Connection, column_id: str, title: str | None, position: int | None
) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        UPDATE board_columns
        SET title = coalesce($2, title),
            position = coalesce($3, position),
            updated_at = now()
        WHERE id = $1
        RETURNING {_COLUMN}
        """,
        column_id,
        title,
        position,
    )
    if not row:
        raise NotFound("Column", column_id)
    return dict(row)


async def delete_column(conn: asyncpg.Connection, column_id: str) -> None:
    deleted = await conn.fetchval("DELETE FROM board_columns WHERE id = $1 RETURNING id", column_id)
    if not deleted:
        raise NotFound("Column", column_id)


async def create_card(
    conn: asyncpg.Connection, column_id: str, title: str, body: dict[str, Any]
) -> dict[str, Any]:
    await _require_column(conn, column_id)
    row = await conn.fetchrow(
        f"""
        INSERT INTO cards (id, column_id, title, position, body)
        VALUES ($1, $2, $3,
                (SELECT coalesce(max(position) + 1, 0) FROM cards WHERE column_id = $2), $4)
        RETURNING {_CARD}
        """,
        str(ULID()),
        column_id,
        title,
        body,
    )
    return dict(row)


async def update_card(
    conn: asyncpg.Connection,
    card_id: str,
    title: str | None,
    column_id: str | None,
    position: int | None,
    body: dict[str, Any] | None,
) -> dict[str, Any]:
    if column_id is not None:
        await _require_column(conn, column_id)
    row = await conn.fetchrow(
        f"""
        UPDATE cards
        SET title = coalesce($2, title),
            column_id = coalesce($3, column_id),
            position = CASE
                WHEN $4::int IS NOT NULL THEN $4::int
                WHEN $3::text IS NOT NULL AND $3 <> column_id
                    THEN (SELECT coalesce(max(position) + 1, 0) FROM cards WHERE column_id = $3)
                ELSE position
            END,
            body = coalesce($5, body),
            updated_at = now()
        WHERE id = $1
        RETURNING {_CARD}
        """,
        card_id,
        title,
        column_id,
        position,
        body,
    )
    if not row:
        raise NotFound("Card", card_id)
    return dict(row)


async def delete_card(conn: asyncpg.Connection, card_id: str) -> None:
    deleted = await conn.fetchval("DELETE FROM cards WHERE id = $1 RETURNING id", card_id)
    if not deleted:
        raise NotFound("Card", card_id)


async def _require_column(conn: asyncpg.Connection, column_id: str) -> None:
    if not await conn.fetchval("SELECT 1 FROM board_columns WHERE id = $1", column_id):
        raise NotFound("Column", column_id)
