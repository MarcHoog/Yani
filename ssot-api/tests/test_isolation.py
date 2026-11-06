"""Auth and tenant isolation. docs/architecture.md section 2."""

from httpx import AsyncClient

from tests.conftest import OPERATOR_TID, Customer, issuer, new_customer, operator_headers


async def test_no_token_is_401(client: AsyncClient) -> None:
    for method, path in [
        ("GET", "/api/v1/catalog"),
        ("GET", "/api/v1/nodes"),
        ("POST", "/api/v1/nodes"),
        ("GET", "/api/v1/nodes/x"),
        ("PATCH", "/api/v1/nodes/x"),
        ("DELETE", "/api/v1/nodes/x"),
        ("GET", "/api/v1/nodes/x/relations"),
        ("POST", "/api/v1/relations"),
        ("DELETE", "/api/v1/relations"),
    ]:
        r = await client.request(method, path)
        assert r.status_code == 401, (method, path)


async def test_wrong_audience_is_401(client: AsyncClient) -> None:
    headers = issuer.headers(OPERATOR_TID, "operator-user", audience="api://other-app")
    assert (await client.get("/api/v1/catalog", headers=headers)).status_code == 401


async def test_unmapped_tenant_is_403(client: AsyncClient) -> None:
    r = await client.get("/api/v1/catalog", headers=issuer.headers("unknown-tenant", "u"))
    assert r.status_code == 403


async def test_customer_resolved_through_todo_api(client: AsyncClient) -> None:
    r = await client.get("/api/v1/catalog", headers=new_customer().headers)
    assert r.status_code == 200


async def test_customers_cannot_write_inventory(client: AsyncClient) -> None:
    h = new_customer().headers
    node = {"label": "Group", "name": "x"}
    rel = {"from_id": "a", "type": "MEMBER_OF", "to_id": "b"}
    assert (await client.post("/api/v1/nodes", json=node, headers=h)).status_code == 403
    assert (await client.patch("/api/v1/nodes/x", json={"name": "y"}, headers=h)).status_code == 403
    assert (await client.delete("/api/v1/nodes/x", headers=h)).status_code == 403
    assert (await client.post("/api/v1/relations", json=rel, headers=h)).status_code == 403
    r = await client.request("DELETE", "/api/v1/relations", json=rel, headers=h)
    assert r.status_code == 403


async def test_operator_must_pass_customer_id_when_creating(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/nodes", json={"label": "Group", "name": "x"}, headers=operator_headers()
    )
    assert r.status_code == 422


async def _node(client: AsyncClient, customer: Customer, label: str, name: str) -> dict:
    r = await client.post(
        "/api/v1/nodes",
        json={"customer_id": customer.customer_id, "label": label, "name": name},
        headers=operator_headers(),
    )
    assert r.status_code == 201
    return r.json()


async def test_inventory_isolation(
    client: AsyncClient, customers: tuple[Customer, Customer]
) -> None:
    a, b = customers
    op = operator_headers()
    cust_a = await _node(client, a, "Customer", "A")
    tenant_a = await _node(client, a, "Tenant", "a.onmicrosoft.com")
    cust_b = await _node(client, b, "Customer", "B")
    tenant_b = await _node(client, b, "Tenant", "b.onmicrosoft.com")
    assert cust_a["customer_id"] == a.customer_id

    rel = {"from_id": cust_a["id"], "type": "HAS_TENANT", "to_id": tenant_a["id"]}
    assert (await client.post("/api/v1/relations", json=rel, headers=op)).status_code == 204
    rel = {"from_id": cust_b["id"], "type": "HAS_TENANT", "to_id": tenant_b["id"]}
    assert (await client.post("/api/v1/relations", json=rel, headers=op)).status_code == 204
    # Relations never cross customers, not even for the operator.
    rel = {"from_id": cust_a["id"], "type": "HAS_TENANT", "to_id": tenant_b["id"]}
    assert (await client.post("/api/v1/relations", json=rel, headers=op)).status_code == 400

    # A sees only A.
    r = await client.get("/api/v1/nodes", headers=a.headers)
    assert {n["id"] for n in r.json()} == {cust_a["id"], tenant_a["id"]}
    r = await client.get("/api/v1/nodes?label=Tenant&q=onmicrosoft", headers=a.headers)
    assert [n["id"] for n in r.json()] == [tenant_a["id"]]
    r = await client.get(f"/api/v1/nodes?customer_id={b.customer_id}", headers=a.headers)
    assert r.status_code == 403
    assert (await client.get(f"/api/v1/nodes/{cust_a['id']}", headers=a.headers)).status_code == 200
    r = await client.get(f"/api/v1/nodes/{cust_a['id']}/relations", headers=a.headers)
    assert [m["id"] for m in r.json()["relations"]] == [tenant_a["id"]]

    # A cannot read or write B's nodes.
    assert (await client.get(f"/api/v1/nodes/{cust_b['id']}", headers=a.headers)).status_code == 404
    r = await client.get(f"/api/v1/nodes/{cust_b['id']}/relations", headers=a.headers)
    assert r.status_code == 404
    r = await client.patch(f"/api/v1/nodes/{cust_b['id']}", json={"name": "x"}, headers=a.headers)
    assert r.status_code == 403
    assert (
        await client.delete(f"/api/v1/nodes/{cust_b['id']}", headers=a.headers)
    ).status_code == 403
    r = await client.get(f"/api/v1/nodes/{cust_b['id']}", headers=b.headers)
    assert r.json()["name"] == "B"

    # The operator sees both and can filter.
    ids = {n["id"] for n in (await client.get("/api/v1/nodes", headers=op)).json()}
    assert {cust_a["id"], tenant_a["id"], cust_b["id"], tenant_b["id"]} <= ids
    r = await client.get(f"/api/v1/nodes?customer_id={b.customer_id}", headers=op)
    assert {n["id"] for n in r.json()} == {cust_b["id"], tenant_b["id"]}
    assert (await client.get(f"/api/v1/nodes/{cust_a['id']}", headers=op)).status_code == 200
