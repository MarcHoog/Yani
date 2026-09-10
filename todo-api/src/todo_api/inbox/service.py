from datetime import UTC, datetime
from typing import Any

import asyncpg
from ulid import ULID

from todo_api.board import service as board
from todo_api.exceptions import NotFound

_ITEM = "id, title, position, body, created_at, updated_at"


async def list_items(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(f"SELECT {_ITEM} FROM inbox_items ORDER BY position, id")
    return [dict(row) for row in rows]


async def create_item(conn: asyncpg.Connection, title: str, body: dict[str, Any]) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        INSERT INTO inbox_items (id, title, position, body)
        VALUES ($1, $2, (SELECT coalesce(max(position) + 1, 0) FROM inbox_items), $3)
        RETURNING {_ITEM}
        """,
        str(ULID()),
        title,
        body,
    )
    return dict(row)


async def update_item(
    conn: asyncpg.Connection,
    item_id: str,
    title: str | None,
    position: int | None,
    body: dict[str, Any] | None,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        UPDATE inbox_items
        SET title = coalesce($2, title),
            position = coalesce($3, position),
            body = coalesce($4, body),
            updated_at = now()
        WHERE id = $1
        RETURNING {_ITEM}
        """,
        item_id,
        title,
        position,
        body,
    )
    if not row:
        raise NotFound("Inbox item", item_id)
    return dict(row)


async def delete_item(conn: asyncpg.Connection, item_id: str) -> None:
    deleted = await conn.fetchval("DELETE FROM inbox_items WHERE id = $1 RETURNING id", item_id)
    if not deleted:
        raise NotFound("Inbox item", item_id)


async def promote_item(conn: asyncpg.Connection, item_id: str, column_id: str) -> dict[str, Any]:
    async with conn.transaction():
        item = await _take_item(conn, item_id)
        return await board.create_card(conn, column_id, item["title"], item["body"])


async def attach_item(conn: asyncpg.Connection, item_id: str, card_id: str) -> dict[str, Any]:
    async with conn.transaction():
        item = await _take_item(conn, item_id)
        card_body = await conn.fetchval("SELECT body FROM cards WHERE id = $1 FOR UPDATE", card_id)
        if card_body is None:
            raise NotFound("Card", card_id)
        return await board.update_card(
            conn, card_id, None, None, None, _attach_body(card_body, item)
        )


async def _take_item(conn: asyncpg.Connection, item_id: str) -> dict[str, Any]:
    row = await conn.fetchrow(f"DELETE FROM inbox_items WHERE id = $1 RETURNING {_ITEM}", item_id)
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
