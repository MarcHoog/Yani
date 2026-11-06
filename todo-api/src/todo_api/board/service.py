"""Board SQL. `scope` is the caller's customer filter: a customer_id, or None for all (operator).

Rows outside the scope are reported as not found, never as forbidden, so ids do not leak.
"""

from typing import Any

import asyncpg
from ulid import ULID

from todo_api.exceptions import NotFound

_COLUMN = "id, customer_id, title, position, created_at, updated_at"
_CARD = "id, customer_id, column_id, title, position, body, created_at, updated_at"
_IN_SCOPE = "($2::text IS NULL OR customer_id = $2)"


async def get_board(conn: asyncpg.Connection, scope: str | None) -> dict[str, Any]:
    columns = await conn.fetch(
        f"""
        SELECT {_COLUMN} FROM board_columns
        WHERE ($1::text IS NULL OR customer_id = $1)
        ORDER BY customer_id, position, id
        """,
        scope,
    )
    cards = await conn.fetch(
        f"""
        SELECT {_CARD} FROM cards
        WHERE ($1::text IS NULL OR customer_id = $1)
        ORDER BY position, id
        """,
        scope,
    )
    by_column: dict[str, list[dict[str, Any]]] = {column["id"]: [] for column in columns}
    for card in cards:
        by_column[card["column_id"]].append(dict(card))
    return {"columns": [dict(column) | {"cards": by_column[column["id"]]} for column in columns]}


async def create_column(conn: asyncpg.Connection, customer_id: str, title: str) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        INSERT INTO board_columns (id, customer_id, title, position)
        VALUES ($1, $2, $3,
                (SELECT coalesce(max(position) + 1, 0) FROM board_columns WHERE customer_id = $2))
        RETURNING {_COLUMN}
        """,
        str(ULID()),
        customer_id,
        title,
    )
    return dict(row)


async def update_column(
    conn: asyncpg.Connection,
    scope: str | None,
    column_id: str,
    title: str | None,
    position: int | None,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        UPDATE board_columns
        SET title = coalesce($3, title),
            position = coalesce($4, position),
            updated_at = now()
        WHERE id = $1 AND {_IN_SCOPE}
        RETURNING {_COLUMN}
        """,
        column_id,
        scope,
        title,
        position,
    )
    if not row:
        raise NotFound("Column", column_id)
    return dict(row)


async def delete_column(conn: asyncpg.Connection, scope: str | None, column_id: str) -> None:
    deleted = await conn.fetchval(
        f"DELETE FROM board_columns WHERE id = $1 AND {_IN_SCOPE} RETURNING id", column_id, scope
    )
    if not deleted:
        raise NotFound("Column", column_id)


async def create_card(
    conn: asyncpg.Connection, customer_id: str, column_id: str, title: str, body: dict[str, Any]
) -> dict[str, Any]:
    await _require_column(conn, customer_id, column_id)
    row = await conn.fetchrow(
        f"""
        INSERT INTO cards (id, customer_id, column_id, title, position, body)
        VALUES ($1, $2, $3, $4,
                (SELECT coalesce(max(position) + 1, 0) FROM cards WHERE column_id = $3), $5)
        RETURNING {_CARD}
        """,
        str(ULID()),
        customer_id,
        column_id,
        title,
        body,
    )
    return dict(row)


async def update_card(
    conn: asyncpg.Connection,
    scope: str | None,
    card_id: str,
    title: str | None,
    column_id: str | None,
    position: int | None,
    body: dict[str, Any] | None,
) -> dict[str, Any]:
    if column_id is not None:
        # The target column must belong to the card's own customer.
        owner = await conn.fetchval(
            f"SELECT customer_id FROM cards WHERE id = $1 AND {_IN_SCOPE}", card_id, scope
        )
        if owner is None:
            raise NotFound("Card", card_id)
        await _require_column(conn, owner, column_id)
    row = await conn.fetchrow(
        f"""
        UPDATE cards
        SET title = coalesce($3, title),
            column_id = coalesce($4, column_id),
            position = CASE
                WHEN $5::int IS NOT NULL THEN $5::int
                WHEN $4::text IS NOT NULL AND $4 <> column_id
                    THEN (SELECT coalesce(max(position) + 1, 0) FROM cards WHERE column_id = $4)
                ELSE position
            END,
            body = coalesce($6, body),
            updated_at = now()
        WHERE id = $1 AND {_IN_SCOPE}
        RETURNING {_CARD}
        """,
        card_id,
        scope,
        title,
        column_id,
        position,
        body,
    )
    if not row:
        raise NotFound("Card", card_id)
    return dict(row)


async def delete_card(conn: asyncpg.Connection, scope: str | None, card_id: str) -> None:
    deleted = await conn.fetchval(
        f"DELETE FROM cards WHERE id = $1 AND {_IN_SCOPE} RETURNING id", card_id, scope
    )
    if not deleted:
        raise NotFound("Card", card_id)


async def _require_column(conn: asyncpg.Connection, customer_id: str, column_id: str) -> None:
    if not await conn.fetchval(
        "SELECT 1 FROM board_columns WHERE id = $1 AND customer_id = $2", column_id, customer_id
    ):
        raise NotFound("Column", column_id)
