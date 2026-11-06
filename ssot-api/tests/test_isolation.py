"""Auth and tenant isolation. docs/architecture.md section 2."""

from httpx import AsyncClient

from tests.conftest import issuer

OP = issuer.operator_headers()


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


async def test_wrong_issuer_or_audience_is_401(client: AsyncClient) -> None:
    for headers in (
        issuer.operator_headers(audience="other-project"),
        issuer.operator_headers(issuer="http://evil.test"),
    ):
        assert (await client.get("/api/v1/catalog", headers=headers)).status_code == 401


async def test_token_without_yani_role_is_403(client: AsyncClient) -> None:
    headers = {"Authorization": f"Bearer {issuer.token(None)}"}
    assert (await client.get("/api/v1/catalog", headers=headers)).status_code == 403


async def test_customers_cannot_write_inventory(client: AsyncClient) -> None:
    h = issuer.customer_headers("org-a")
    node = {"label": "Group", "name": "x"}
    rel = {"from_id": "a", "type": "MEMBER_OF", "to_id": "b"}
    assert (await client.post("/api/v1/nodes", json=node, headers=h)).status_code == 403
    assert (await client.patch("/api/v1/nodes/x", json={"name": "y"}, headers=h)).status_code == 403
    assert (await client.delete("/api/v1/nodes/x", headers=h)).status_code == 403
    assert (await client.post("/api/v1/relations", json=rel, headers=h)).status_code == 403
    r = await client.request("DELETE", "/api/v1/relations", json=rel, headers=h)
    assert r.status_code == 403


async def test_operator_must_pass_customer_id_when_creating(client: AsyncClient) -> None:
    r = await client.post("/api/v1/nodes", json={"label": "Group", "name": "x"}, headers=OP)
    assert r.status_code == 422


async def _node(client: AsyncClient, customer_id: str, label: str, name: str) -> dict:
    r = await client.post(
        "/api/v1/nodes",
        json={"customer_id": customer_id, "label": label, "name": name},
        headers=OP,
    )
    assert r.status_code == 201
    return r.json()


async def test_inventory_isolation(client: AsyncClient, customers: tuple[str, str]) -> None:
    a, b = customers
    ha, hb = issuer.customer_headers(a), issuer.customer_headers(b)
    cust_a = await _node(client, a, "Customer", "A")
    tenant_a = await _node(client, a, "Tenant", "a.onmicrosoft.com")
    cust_b = await _node(client, b, "Customer", "B")
    tenant_b = await _node(client, b, "Tenant", "b.onmicrosoft.com")
    assert cust_a["customer_id"] == a

    rel = {"from_id": cust_a["id"], "type": "HAS_TENANT", "to_id": tenant_a["id"]}
    assert (await client.post("/api/v1/relations", json=rel, headers=OP)).status_code == 204
    rel = {"from_id": cust_b["id"], "type": "HAS_TENANT", "to_id": tenant_b["id"]}
    assert (await client.post("/api/v1/relations", json=rel, headers=OP)).status_code == 204
    # Relations never cross customers, not even for the operator.
    rel = {"from_id": cust_a["id"], "type": "HAS_TENANT", "to_id": tenant_b["id"]}
    assert (await client.post("/api/v1/relations", json=rel, headers=OP)).status_code == 400

    # A sees only A.
    r = await client.get("/api/v1/nodes", headers=ha)
    assert {n["id"] for n in r.json()} == {cust_a["id"], tenant_a["id"]}
    r = await client.get("/api/v1/nodes?label=Tenant&q=onmicrosoft", headers=ha)
    assert [n["id"] for n in r.json()] == [tenant_a["id"]]
    r = await client.get(f"/api/v1/nodes?customer_id={b}", headers=ha)
    assert r.status_code == 403
    assert (await client.get(f"/api/v1/nodes/{cust_a['id']}", headers=ha)).status_code == 200
    r = await client.get(f"/api/v1/nodes/{cust_a['id']}/relations", headers=ha)
    assert [m["id"] for m in r.json()["relations"]] == [tenant_a["id"]]

    # A cannot read or write B's nodes.
    assert (await client.get(f"/api/v1/nodes/{cust_b['id']}", headers=ha)).status_code == 404
    r = await client.get(f"/api/v1/nodes/{cust_b['id']}/relations", headers=ha)
    assert r.status_code == 404
    r = await client.patch(f"/api/v1/nodes/{cust_b['id']}", json={"name": "x"}, headers=ha)
    assert r.status_code == 403
    assert (await client.delete(f"/api/v1/nodes/{cust_b['id']}", headers=ha)).status_code == 403
    r = await client.get(f"/api/v1/nodes/{cust_b['id']}", headers=hb)
    assert r.json()["name"] == "B"

    # The operator sees both and can filter.
    ids = {n["id"] for n in (await client.get("/api/v1/nodes", headers=OP)).json()}
    assert {cust_a["id"], tenant_a["id"], cust_b["id"], tenant_b["id"]} <= ids
    r = await client.get(f"/api/v1/nodes?customer_id={b}", headers=OP)
    assert {n["id"] for n in r.json()} == {cust_b["id"], tenant_b["id"]}
    assert (await client.get(f"/api/v1/nodes/{cust_a['id']}", headers=OP)).status_code == 200
