"""Reads are scoped to the caller's customer. Writes are operator only: customers read inventory,
they never change it (docs/architecture.md section 2)."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from ssot_api.auth import CallerDep
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
    caller: CallerDep,
    label: Annotated[Label | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    customer_id: Annotated[str | None, Query()] = None,
) -> list[NodeRead]:
    return await service.list_nodes(session, caller.scope(customer_id), label, q)


@router.post("/nodes", status_code=status.HTTP_201_CREATED)
async def create_node(session: SessionDep, caller: CallerDep, payload: NodeCreate) -> NodeRead:
    caller.require_operator()
    customer_id = caller.owner(payload.customer_id)
    return await service.create_node(session, customer_id, payload.label, payload.name)


@router.get("/nodes/{node_id}")
async def get_node(session: SessionDep, caller: CallerDep, node_id: str) -> NodeRead:
    return await service.get_node(session, caller.scope(), node_id)


@router.patch("/nodes/{node_id}")
async def update_node(
    session: SessionDep, caller: CallerDep, node_id: str, payload: NodeUpdate
) -> NodeRead:
    caller.require_operator()
    return await service.update_node(session, node_id, payload.name)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(session: SessionDep, caller: CallerDep, node_id: str) -> None:
    caller.require_operator()
    await service.delete_node(session, node_id)


@router.get("/nodes/{node_id}/relations")
async def get_relations(session: SessionDep, caller: CallerDep, node_id: str) -> NodeRelations:
    return await service.get_relations(session, caller.scope(), node_id)


@router.post("/relations", status_code=status.HTTP_204_NO_CONTENT)
async def create_relation(session: SessionDep, caller: CallerDep, payload: RelationRef) -> None:
    caller.require_operator()
    await service.create_relation(session, payload.from_id, payload.type, payload.to_id)


@router.delete("/relations", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(session: SessionDep, caller: CallerDep, payload: RelationRef) -> None:
    caller.require_operator()
    await service.delete_relation(session, payload.from_id, payload.type, payload.to_id)
