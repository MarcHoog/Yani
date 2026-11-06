"""Cypher. `scope` is the caller's customer filter: a customer_id, or None for all (operator).

Nodes outside the scope are reported as not found, so ids do not leak across customers.
"""

from datetime import UTC, datetime
from typing import Any

from neo4j import AsyncSession
from ulid import ULID

from ssot_api.database import run
from ssot_api.exceptions import InvalidRelation, NotFound
from ssot_api.graph import catalog

_NODE = "n {.*, label: labels(n)[0]}"
_IN_SCOPE = "($scope IS NULL OR n.customer_id = $scope)"


def _now() -> str:
    return datetime.now(UTC).isoformat()


async def list_nodes(
    session: AsyncSession, scope: str | None, label: str | None, q: str | None
) -> list[dict]:
    match = f"MATCH (n:{label})" if label else "MATCH (n)"
    where = f"WHERE {_IN_SCOPE}"
    if q:
        where += " AND toLower(n.name) CONTAINS toLower($q)"
    rows = await run(
        session, f"{match} {where} RETURN {_NODE} AS n ORDER BY n.name", scope=scope, q=q or ""
    )
    return [r["n"] for r in rows]


async def get_node(session: AsyncSession, scope: str | None, node_id: str) -> dict:
    rows = await run(
        session,
        f"MATCH (n {{id: $id}}) WHERE {_IN_SCOPE} RETURN {_NODE} AS n",
        id=node_id,
        scope=scope,
    )
    if not rows:
        raise NotFound("Node", node_id)
    return rows[0]["n"]


async def create_node(session: AsyncSession, customer_id: str, label: str, name: str) -> dict:
    now = _now()
    props: dict[str, Any] = {
        "id": str(ULID()),
        "customer_id": customer_id,
        "name": name,
        "created_at": now,
        "updated_at": now,
    }
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


async def get_relations(session: AsyncSession, scope: str | None, node_id: str) -> dict:
    node = await get_node(session, scope, node_id)
    rows = await run(
        session,
        """
        MATCH (n {id: $id})-[r]-(m)
        WHERE $scope IS NULL OR m.customer_id = $scope
        RETURN m {.*, label: labels(m)[0], relation: type(r),
                  direction: CASE WHEN startNode(r) = n THEN 'out' ELSE 'in' END} AS m
        ORDER BY m.relation, m.label, m.name
        """,
        id=node_id,
        scope=scope,
    )
    return {"node": node, "relations": [r["m"] for r in rows]}


async def create_relation(session: AsyncSession, from_id: str, rel: str, to_id: str) -> None:
    a = await get_node(session, None, from_id)
    b = await get_node(session, None, to_id)
    if not catalog.is_allowed(a["label"], rel, b["label"]):
        raise InvalidRelation(f"{a['label']}-[:{rel}]->{b['label']} not in catalog")
    if a["customer_id"] != b["customer_id"]:
        raise InvalidRelation("Relations never cross customers")
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
