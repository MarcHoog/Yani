from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from todo_api.board.schemas import Strict


class InboxItemCreate(Strict):
    title: str = Field(min_length=1, max_length=300)
    body: dict[str, Any] = Field(default_factory=dict)


class InboxItemUpdate(Strict):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    position: int | None = Field(default=None, ge=0)
    body: dict[str, Any] | None = None


class InboxItemRead(BaseModel):
    id: str
    title: str
    position: int
    body: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class InboxPromote(Strict):
    column_id: str


class InboxAttach(Strict):
    card_id: str
