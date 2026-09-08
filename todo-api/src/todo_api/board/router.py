from fastapi import APIRouter, status

from todo_api.board import service
from todo_api.board.schemas import (
    Board,
    CardCreate,
    CardRead,
    CardUpdate,
    ColumnCreate,
    ColumnRead,
    ColumnUpdate,
)
from todo_api.database import ConnDep

router = APIRouter(tags=["board"])


@router.get("/board")
async def get_board(conn: ConnDep) -> Board:
    return Board(**await service.get_board(conn))


@router.post("/columns", status_code=status.HTTP_201_CREATED)
async def create_column(conn: ConnDep, payload: ColumnCreate) -> ColumnRead:
    return ColumnRead(**await service.create_column(conn, payload.title))


@router.patch("/columns/{column_id}")
async def update_column(conn: ConnDep, column_id: str, payload: ColumnUpdate) -> ColumnRead:
    return ColumnRead(
        **await service.update_column(conn, column_id, payload.title, payload.position)
    )


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(conn: ConnDep, column_id: str) -> None:
    await service.delete_column(conn, column_id)


@router.post("/cards", status_code=status.HTTP_201_CREATED)
async def create_card(conn: ConnDep, payload: CardCreate) -> CardRead:
    return CardRead(
        **await service.create_card(conn, payload.column_id, payload.title, payload.body)
    )


@router.patch("/cards/{card_id}")
async def update_card(conn: ConnDep, card_id: str, payload: CardUpdate) -> CardRead:
    return CardRead(
        **await service.update_card(
            conn, card_id, payload.title, payload.column_id, payload.position, payload.body
        )
    )


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(conn: ConnDep, card_id: str) -> None:
    await service.delete_card(conn, card_id)
