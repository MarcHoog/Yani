"""Auth and tenant isolation. docs/architecture.md section 2."""

from httpx import AsyncClient

from tests.conftest import OPERATOR_TID, Customer, issuer, operator_headers


async def test_no_token_is_401(client: AsyncClient) -> None:
    for method, path in [
        ("GET", "/api/v1/me"),
        ("GET", "/api/v1/board"),
        ("POST", "/api/v1/columns"),
        ("PATCH", "/api/v1/cards/x"),
        ("DELETE", "/api/v1/cards/x"),
        ("GET", "/api/v1/inbox"),
        ("POST", "/api/v1/inbox/x/promote"),
    ]:
        r = await client.request(method, path)
        assert r.status_code == 401, (method, path)
        assert r.headers["www-authenticate"] == "Bearer"


async def test_wrong_audience_is_401(client: AsyncClient) -> None:
    headers = issuer.headers(OPERATOR_TID, "operator-user", audience="api://other-app")
    r = await client.get("/api/v1/board", headers=headers)
    assert r.status_code == 401


async def test_operator_tenant_account_not_allow_listed_is_403(client: AsyncClient) -> None:
    r = await client.get("/api/v1/me", headers=issuer.headers(OPERATOR_TID, "someone-else"))
    assert r.status_code == 403


async def test_health_is_open(client: AsyncClient) -> None:
    assert (await client.get("/health")).status_code == 200


async def test_unmapped_tenant_is_403(
    client: AsyncClient, customers: tuple[Customer, Customer]
) -> None:
    r = await client.get("/api/v1/board", headers=issuer.headers("unknown-tenant", "u"))
    assert r.status_code == 403


async def test_me_maps_tenant_to_customer(
    client: AsyncClient, customers: tuple[Customer, Customer]
) -> None:
    a, _ = customers
    r = await client.get("/api/v1/me", headers=a.headers)
    assert r.status_code == 200
    assert r.json()["role"] == "customer"
    assert r.json()["customer_id"] == a.customer_id

    r = await client.get("/api/v1/me", headers=operator_headers())
    assert r.json() == {
        "role": "operator",
        "tenant_id": OPERATOR_TID,
        "object_id": "operator-user",
        "customer_id": None,
    }


async def test_operator_must_pass_customer_id_when_creating(
    client: AsyncClient, customers: tuple[Customer, Customer]
) -> None:
    h = operator_headers()
    assert (await client.post("/api/v1/columns", json={"title": "x"}, headers=h)).status_code == 422
    assert (await client.post("/api/v1/inbox", json={"title": "x"}, headers=h)).status_code == 422


async def test_board_isolation(client: AsyncClient, customers: tuple[Customer, Customer]) -> None:
    a, b = customers
    op = operator_headers()

    col_a = (
        await client.post(
            "/api/v1/columns", json={"customer_id": a.customer_id, "title": "A"}, headers=op
        )
    ).json()
    col_b = (
        await client.post(
            "/api/v1/columns", json={"customer_id": b.customer_id, "title": "B"}, headers=op
        )
    ).json()
    assert col_a["customer_id"] == a.customer_id
    # A customer creating without customer_id gets their own.
    r = await client.post(
        "/api/v1/cards", json={"column_id": col_a["id"], "title": "a1"}, headers=a.headers
    )
    assert r.status_code == 201
    card_a = r.json()
    assert card_a["customer_id"] == a.customer_id
    r = await client.post(
        "/api/v1/cards",
        json={"customer_id": b.customer_id, "column_id": col_b["id"], "title": "b1"},
        headers=op,
    )
    card_b = r.json()

    # Reads: each customer sees only their own board.
    board_a = (await client.get("/api/v1/board", headers=a.headers)).json()
    assert [c["id"] for c in board_a["columns"]] == [col_a["id"]]
    assert [c["id"] for c in board_a["columns"][0]["cards"]] == [card_a["id"]]
    r = await client.get(f"/api/v1/board?customer_id={b.customer_id}", headers=a.headers)
    assert r.status_code == 403

    # Writes against B's rows from A: not found, and B's rows are untouched.
    assert (
        await client.patch(f"/api/v1/columns/{col_b['id']}", json={"title": "x"}, headers=a.headers)
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/columns/{col_b['id']}", headers=a.headers)
    ).status_code == 404
    assert (
        await client.patch(f"/api/v1/cards/{card_b['id']}", json={"title": "x"}, headers=a.headers)
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/cards/{card_b['id']}", headers=a.headers)
    ).status_code == 404
    # A cannot put a card in B's column, by omission or by naming B.
    r = await client.post(
        "/api/v1/cards", json={"column_id": col_b["id"], "title": "x"}, headers=a.headers
    )
    assert r.status_code == 404
    r = await client.post(
        "/api/v1/cards",
        json={"customer_id": b.customer_id, "column_id": col_b["id"], "title": "x"},
        headers=a.headers,
    )
    assert r.status_code == 403
    # A cannot move its own card into B's column.
    r = await client.patch(
        f"/api/v1/cards/{card_a['id']}", json={"column_id": col_b["id"]}, headers=a.headers
    )
    assert r.status_code == 404
    # Neither can the operator: cards never cross customers.
    r = await client.patch(
        f"/api/v1/cards/{card_a['id']}", json={"column_id": col_b["id"]}, headers=op
    )
    assert r.status_code == 404

    board_b = (await client.get("/api/v1/board", headers=b.headers)).json()
    assert [c["title"] for c in board_b["columns"]] == ["B"]
    assert [c["title"] for c in board_b["columns"][0]["cards"]] == ["b1"]

    # Operator sees both, and can filter.
    all_ids = {c["id"] for c in (await client.get("/api/v1/board", headers=op)).json()["columns"]}
    assert {col_a["id"], col_b["id"]} <= all_ids
    r = await client.get(f"/api/v1/board?customer_id={b.customer_id}", headers=op)
    assert [c["id"] for c in r.json()["columns"]] == [col_b["id"]]


async def test_inbox_isolation(client: AsyncClient, customers: tuple[Customer, Customer]) -> None:
    a, b = customers
    op = operator_headers()
    col_b = (
        await client.post(
            "/api/v1/columns", json={"customer_id": b.customer_id, "title": "B"}, headers=op
        )
    ).json()
    card_b = (
        await client.post(
            "/api/v1/cards", json={"column_id": col_b["id"], "title": "b"}, headers=b.headers
        )
    ).json()
    item_a = (await client.post("/api/v1/inbox", json={"title": "a"}, headers=a.headers)).json()
    assert item_a["customer_id"] == a.customer_id
    item_b = (await client.post("/api/v1/inbox", json={"title": "b"}, headers=b.headers)).json()

    assert [i["id"] for i in (await client.get("/api/v1/inbox", headers=a.headers)).json()] == [
        item_a["id"]
    ]
    assert (
        await client.get(f"/api/v1/inbox?customer_id={b.customer_id}", headers=a.headers)
    ).status_code == 403

    # A cannot touch B's item.
    for method, path, body in [
        ("PATCH", f"/api/v1/inbox/{item_b['id']}", {"title": "x"}),
        ("DELETE", f"/api/v1/inbox/{item_b['id']}", None),
        ("POST", f"/api/v1/inbox/{item_b['id']}/promote", {"column_id": col_b["id"]}),
        ("POST", f"/api/v1/inbox/{item_b['id']}/attach", {"card_id": card_b["id"]}),
    ]:
        r = await client.request(method, path, json=body, headers=a.headers)
        assert r.status_code == 404, (method, path)

    # A cannot push its own item into B's column or card; the item survives (rolled back).
    r = await client.post(
        f"/api/v1/inbox/{item_a['id']}/promote", json={"column_id": col_b["id"]}, headers=a.headers
    )
    assert r.status_code == 404
    r = await client.post(
        f"/api/v1/inbox/{item_a['id']}/attach", json={"card_id": card_b["id"]}, headers=a.headers
    )
    assert r.status_code == 404
    assert [i["id"] for i in (await client.get("/api/v1/inbox", headers=a.headers)).json()] == [
        item_a["id"]
    ]
    assert [i["id"] for i in (await client.get("/api/v1/inbox", headers=b.headers)).json()] == [
        item_b["id"]
    ]

    # Operator sees both; B can still promote its own item.
    all_ids = {i["id"] for i in (await client.get("/api/v1/inbox", headers=op)).json()}
    assert {item_a["id"], item_b["id"]} <= all_ids
    r = await client.post(
        f"/api/v1/inbox/{item_b['id']}/promote", json={"column_id": col_b["id"]}, headers=b.headers
    )
    assert r.status_code == 201
    assert r.json()["customer_id"] == b.customer_id
