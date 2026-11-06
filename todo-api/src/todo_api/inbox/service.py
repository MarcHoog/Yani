"""Inbox SQL. `scope` is the caller's customer filter, as in board/service.py."""

from datetime import UTC, datetime
from typing import Any

import asyncpg
from ulid import ULID

from todo_api.board import service as board
from todo_api.exceptions import NotFound

_ITEM = "id, customer_id, title, position, body, created_at, updated_at"
_IN_SCOPE = "($2::text IS NULL OR customer_id = $2)"


async def list_items(conn: asyncpg.Connection, scope: str | None) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"""
        SELECT {_ITEM} FROM inbox_items
        WHERE ($1::text IS NULL OR customer_id = $1)
        ORDER BY position, id
        """,
        scope,
    )
    return [dict(row) for row in rows]


async def create_item(
    conn: asyncpg.Connection, customer_id: str, title: str, body: dict[str, Any]
) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        INSERT INTO inbox_items (id, customer_id, title, position, body)
        VALUES ($1, $2, $3,
                (SELECT coalesce(max(position) + 1, 0) FROM inbox_items WHERE customer_id = $2),
                $4)
        RETURNING {_ITEM}
        """,
        str(ULID()),
        customer_id,
        title,
        body,
    )
    return dict(row)


async def update_item(
    conn: asyncpg.Connection,
    scope: str | None,
    item_id: str,
    title: str | None,
    position: int | None,
    body: dict[str, Any] | None,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        UPDATE inbox_items
        SET title = coalesce($3, title),
            position = coalesce($4, position),
            body = coalesce($5, body),
            updated_at = now()
        WHERE id = $1 AND {_IN_SCOPE}
        RETURNING {_ITEM}
        """,
        item_id,
        scope,
        title,
        position,
        body,
    )
    if not row:
        raise NotFound("Inbox item", item_id)
    return dict(row)


async def delete_item(conn: asyncpg.Connection, scope: str | None, item_id: str) -> None:
    deleted = await conn.fetchval(
        f"DELETE FROM inbox_items WHERE id = $1 AND {_IN_SCOPE} RETURNING id", item_id, scope
    )
    if not deleted:
        raise NotFound("Inbox item", item_id)


async def promote_item(
    conn: asyncpg.Connection, scope: str | None, item_id: str, column_id: str
) -> dict[str, Any]:
    async with conn.transaction():
        item = await _take_item(conn, scope, item_id)
        return await board.create_card(
            conn, item["customer_id"], column_id, item["title"], item["body"]
        )


async def attach_item(
    conn: asyncpg.Connection, scope: str | None, item_id: str, card_id: str
) -> dict[str, Any]:
    async with conn.transaction():
        item = await _take_item(conn, scope, item_id)
        card_body = await conn.fetchval(
            "SELECT body FROM cards WHERE id = $1 AND customer_id = $2 FOR UPDATE",
            card_id,
            item["customer_id"],
        )
        if card_body is None:
            raise NotFound("Card", card_id)
        return await board.update_card(
            conn,
            item["customer_id"],
            card_id,
            None,
            None,
            None,
            _attach_body(card_body, item),
        )


async def _take_item(conn: asyncpg.Connection, scope: str | None, item_id: str) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"DELETE FROM inbox_items WHERE id = $1 AND {_IN_SCOPE} RETURNING {_ITEM}", item_id, scope
    )
    if not row:
        raise NotFound("Inbox item", item_id)
    return dict(row)


def _attach_body(card_body: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    todos = list(card_body.get("todos") or [])
    comments = list(card_body.get("comments") or [])
    todos.append({"id": str(ULID()), "text": item["title"], "done": False})
    description = item["body"].get("description")
    if isinstance(description, str) and description.strip():
        comments.append(
            {"id": str(ULID()), "text": description, "at": datetime.now(UTC).isoformat()}
        )
    return card_body | {"todos": todos, "comments": comments}
