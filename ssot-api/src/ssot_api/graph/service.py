from datetime import UTC, datetime
from typing import Any

from neo4j import AsyncSession
from ulid import ULID

from ssot_api.database import run
from ssot_api.exceptions import InvalidRelation, NotFound
from ssot_api.graph import catalog

_NODE = "n {.*, label: labels(n)[0]}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


async def list_nodes(session: AsyncSession, label: str | None, q: str | None) -> list[dict]:
    match = f"MATCH (n:{label})" if label else "MATCH (n)"
    where = "WHERE toLower(n.name) CONTAINS toLower($q)" if q else ""
    rows = await run(session, f"{match} {where} RETURN {_NODE} AS n ORDER BY n.name", q=q or "")
    return [r["n"] for r in rows]


async def get_node(session: AsyncSession, node_id: str) -> dict:
    rows = await run(session, f"MATCH (n {{id: $id}}) RETURN {_NODE} AS n", id=node_id)
    if not rows:
        raise NotFound("Node", node_id)
    return rows[0]["n"]


async def create_node(session: AsyncSession, label: str, name: str) -> dict:
    now = _now()
    props: dict[str, Any] = {"id": str(ULID()), "name": name, "created_at": now, "updated_at": now}
    rows = await run(session, f"CREATE (n:{label} $props) RETURN {_NODE} AS n", props=props)
    return rows[0]["n"]


async def update_node(session: AsyncSession, node_id: str, name: str) -> dict:
    rows = await run(
        session,
        f"MATCH (n {{id: $id}}) SET n.name = $name, n.updated_at = $now RETURN {_NODE} AS n",
        id=node_id,
        name=name,
        now=_now(),
    )
    if not rows:
        raise NotFound("Node", node_id)
    return rows[0]["n"]


async def delete_node(session: AsyncSession, node_id: str) -> None:
    rows = await run(
        session, "MATCH (n {id: $id}) WITH n, n.id AS id DETACH DELETE n RETURN id", id=node_id
    )
    if not rows:
        raise NotFound("Node", node_id)


async def get_relations(session: AsyncSession, node_id: str) -> dict:
    node = await get_node(session, node_id)
    rows = await run(
        session,
        """
        MATCH (n {id: $id})-[r]-(m)
        RETURN m {.*, label: labels(m)[0], relation: type(r),
                  direction: CASE WHEN startNode(r) = n THEN 'out' ELSE 'in' END} AS m
        ORDER BY m.relation, m.label, m.name
        """,
        id=node_id,
    )
    return {"node": node, "relations": [r["m"] for r in rows]}


async def create_relation(session: AsyncSession, from_id: str, rel: str, to_id: str) -> None:
    a = await get_node(session, from_id)
    b = await get_node(session, to_id)
    if not catalog.is_allowed(a["label"], rel, b["label"]):
        raise InvalidRelation(f"{a['label']}-[:{rel}]->{b['label']} not in catalog")
    await run(
        session,
        f"MATCH (a {{id: $a}}), (b {{id: $b}}) MERGE (a)-[:{rel}]->(b)",
        a=from_id,
        b=to_id,
    )


async def delete_relation(session: AsyncSession, from_id: str, rel: str, to_id: str) -> None:
    rows = await run(
        session,
        f"MATCH (a {{id: $a}})-[r:{rel}]->(b {{id: $b}}) WITH r, 1 AS c DELETE r RETURN c",
        a=from_id,
        b=to_id,
    )
    if not rows:
        raise NotFound("Relation", f"{from_id}-[:{rel}]->{to_id}")
