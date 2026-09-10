from fastapi import APIRouter, status

from todo_api.board.schemas import CardRead
from todo_api.database import ConnDep
from todo_api.inbox import service
from todo_api.inbox.schemas import (
    InboxAttach,
    InboxItemCreate,
    InboxItemRead,
    InboxItemUpdate,
    InboxPromote,
)

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("")
async def list_items(conn: ConnDep) -> list[InboxItemRead]:
    return [InboxItemRead(**item) for item in await service.list_items(conn)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_item(conn: ConnDep, payload: InboxItemCreate) -> InboxItemRead:
    return InboxItemRead(**await service.create_item(conn, payload.title, payload.body))


@router.patch("/{item_id}")
async def update_item(conn: ConnDep, item_id: str, payload: InboxItemUpdate) -> InboxItemRead:
    return InboxItemRead(
        **await service.update_item(conn, item_id, payload.title, payload.position, payload.body)
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(conn: ConnDep, item_id: str) -> None:
    await service.delete_item(conn, item_id)


@router.post("/{item_id}/promote", status_code=status.HTTP_201_CREATED)
async def promote_item(conn: ConnDep, item_id: str, payload: InboxPromote) -> CardRead:
    return CardRead(**await service.promote_item(conn, item_id, payload.column_id))


@router.post("/{item_id}/attach")
async def attach_item(conn: ConnDep, item_id: str, payload: InboxAttach) -> CardRead:
    return CardRead(**await service.attach_item(conn, item_id, payload.card_id))
