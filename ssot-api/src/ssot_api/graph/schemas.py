from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ssot_api.graph.catalog import LABELS, RELATION_TYPES

Label = Literal[*LABELS]
RelationType = Literal[*RELATION_TYPES]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class NodeCreate(Strict):
    label: Label
    name: str = Field(min_length=1, max_length=200)


class NodeUpdate(Strict):
    name: str = Field(min_length=1, max_length=200)


class NodeRead(BaseModel):
    id: str
    label: str
    name: str
    created_at: datetime
    updated_at: datetime


class RelationRef(Strict):
    from_id: str
    type: RelationType
    to_id: str


class RelatedNode(NodeRead):
    relation: str
    direction: Literal["out", "in"]


class NodeRelations(BaseModel):
    node: NodeRead
    relations: list[RelatedNode]


class Catalog(BaseModel):
    labels: list[str]
    relations: list[tuple[str, str, str]]
