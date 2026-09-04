from typing import Annotated

from fastapi import APIRouter, Query, status

from ssot_api.database import SessionDep
from ssot_api.graph import catalog, service
from ssot_api.graph.schemas import (
    Catalog,
    Label,
    NodeCreate,
    NodeRead,
    NodeRelations,
    NodeUpdate,
    RelationRef,
)

router = APIRouter(tags=["graph"])


@router.get("/catalog")
async def get_catalog() -> Catalog:
    return Catalog(labels=catalog.LABELS, relations=catalog.RELATION_CATALOG)


@router.get("/nodes")
async def list_nodes(
    session: SessionDep,
    label: Annotated[Label | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> list[NodeRead]:
    return await service.list_nodes(session, label, q)


@router.post("/nodes", status_code=status.HTTP_201_CREATED)
async def create_node(session: SessionDep, payload: NodeCreate) -> NodeRead:
    return await service.create_node(session, payload.label, payload.name)


@router.get("/nodes/{node_id}")
async def get_node(session: SessionDep, node_id: str) -> NodeRead:
    return await service.get_node(session, node_id)


@router.patch("/nodes/{node_id}")
async def update_node(session: SessionDep, node_id: str, payload: NodeUpdate) -> NodeRead:
    return await service.update_node(session, node_id, payload.name)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(session: SessionDep, node_id: str) -> None:
    await service.delete_node(session, node_id)


@router.get("/nodes/{node_id}/relations")
async def get_relations(session: SessionDep, node_id: str) -> NodeRelations:
    return await service.get_relations(session, node_id)


@router.post("/relations", status_code=status.HTTP_204_NO_CONTENT)
async def create_relation(session: SessionDep, payload: RelationRef) -> None:
    await service.create_relation(session, payload.from_id, payload.type, payload.to_id)


@router.delete("/relations", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(session: SessionDep, payload: RelationRef) -> None:
    await service.delete_relation(session, payload.from_id, payload.type, payload.to_id)
