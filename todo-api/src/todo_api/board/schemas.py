from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ColumnCreate(Strict):
    title: str = Field(min_length=1, max_length=120)


class ColumnUpdate(Strict):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    position: int | None = Field(default=None, ge=0)


class CardCreate(Strict):
    column_id: str
    title: str = Field(min_length=1, max_length=300)
    body: dict[str, Any] = Field(default_factory=dict)


class CardUpdate(Strict):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    column_id: str | None = None
    position: int | None = Field(default=None, ge=0)
    body: dict[str, Any] | None = None


class ColumnRead(BaseModel):
    id: str
    title: str
    position: int
    created_at: datetime
    updated_at: datetime


class CardRead(BaseModel):
    id: str
    column_id: str
    title: str
    position: int
    body: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BoardColumn(ColumnRead):
    cards: list[CardRead]


class Board(BaseModel):
    columns: list[BoardColumn]
