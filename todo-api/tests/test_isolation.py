"""Auth and tenant isolation. docs/architecture.md section 2."""

from typing import Any

from httpx import AsyncClient

from tests.conftest import issuer

OP = issuer.operator_headers()


async def test_no_token_is_401(client: AsyncClient) -> None:
    for method, path in [
        ("GET", "/api/v1/board"),
        ("POST", "/api/v1/columns"),
        ("PATCH", "/api/v1/columns/x"),
        ("DELETE", "/api/v1/cards/x"),
        ("GET", "/api/v1/inbox"),
        ("POST", "/api/v1/inbox/x/promote"),
    ]:
        r = await client.request(method, path)
        assert r.status_code == 401, (method, path)
        assert r.headers["www-authenticate"] == "Bearer"


async def test_wrong_issuer_or_audience_is_401(client: AsyncClient) -> None:
    for headers in (
        issuer.operator_headers(audience="other-project"),
        issuer.operator_headers(issuer="http://evil.test"),
    ):
        assert (await client.get("/api/v1/board", headers=headers)).status_code == 401


async def test_token_without_yani_role_is_403(client: AsyncClient) -> None:
    headers = {"Authorization": f"Bearer {issuer.token(None)}"}
    assert (await client.get("/api/v1/board", headers=headers)).status_code == 403


async def test_health_is_open(client: AsyncClient) -> None:
    assert (await client.get("/health")).status_code == 200


async def _post(client: AsyncClient, path: str, body: dict[str, Any]) -> dict[str, Any]:
    r = await client.post(path, json=body, headers=OP)
    assert r.status_code == 201, r.text
    return r.json()


async def test_operator_must_pass_customer_id_when_creating(
    client: AsyncClient, customers: tuple[str, str]
) -> None:
    assert (
        await client.post("/api/v1/columns", json={"title": "x"}, headers=OP)
    ).status_code == 422
    assert (await client.post("/api/v1/inbox", json={"title": "x"}, headers=OP)).status_code == 422


async def test_board_isolation(client: AsyncClient, customers: tuple[str, str]) -> None:
    a, b = customers
    ha, hb = issuer.customer_headers(a), issuer.customer_headers(b)
    col_a = await _post(client, "/api/v1/columns", {"customer_id": a, "title": "A"})
    col_b = await _post(client, "/api/v1/columns", {"customer_id": b, "title": "B"})
    card_a = await _post(
        client, "/api/v1/cards", {"customer_id": a, "column_id": col_a["id"], "title": "a1"}
    )
    card_b = await _post(
        client, "/api/v1/cards", {"customer_id": b, "column_id": col_b["id"], "title": "b1"}
    )
    assert card_a["customer_id"] == a

    # Reads: each customer sees only their own board.
    board_a = (await client.get("/api/v1/board", headers=ha)).json()
    assert [c["id"] for c in board_a["columns"]] == [col_a["id"]]
    assert [c["id"] for c in board_a["columns"][0]["cards"]] == [card_a["id"]]
    r = await client.get(f"/api/v1/board?customer_id={b}", headers=ha)
    assert r.status_code == 403

    # Customers never write: not B's rows, not their own.
    for col, card in ((col_b, card_b), (col_a, card_a)):
        for method, path, body in [
            ("POST", "/api/v1/columns", {"customer_id": b, "title": "x"}),
            ("PATCH", f"/api/v1/columns/{col['id']}", {"title": "x"}),
            ("DELETE", f"/api/v1/columns/{col['id']}", None),
            ("POST", "/api/v1/cards", {"column_id": col["id"], "title": "x"}),
            ("PATCH", f"/api/v1/cards/{card['id']}", {"title": "x"}),
            ("DELETE", f"/api/v1/cards/{card['id']}", None),
        ]:
            r = await client.request(method, path, json=body, headers=ha)
            assert r.status_code == 403, (method, path)

    # Rows never cross customers, not even for the operator.
    r = await client.post(
        "/api/v1/cards", json={"customer_id": a, "column_id": col_b["id"], "title": "x"}, headers=OP
    )
    assert r.status_code == 404
    r = await client.patch(
        f"/api/v1/cards/{card_a['id']}", json={"column_id": col_b["id"]}, headers=OP
    )
    assert r.status_code == 404

    board_b = (await client.get("/api/v1/board", headers=hb)).json()
    assert [c["title"] for c in board_b["columns"]] == ["B"]
    assert [c["title"] for c in board_b["columns"][0]["cards"]] == ["b1"]

    # Operator sees both, and can filter.
    all_ids = {c["id"] for c in (await client.get("/api/v1/board", headers=OP)).json()["columns"]}
    assert {col_a["id"], col_b["id"]} <= all_ids
    r = await client.get(f"/api/v1/board?customer_id={b}", headers=OP)
    assert [c["id"] for c in r.json()["columns"]] == [col_b["id"]]


async def test_inbox_isolation(client: AsyncClient, customers: tuple[str, str]) -> None:
    a, b = customers
    ha, hb = issuer.customer_headers(a), issuer.customer_headers(b)
    col_b = await _post(client, "/api/v1/columns", {"customer_id": b, "title": "B"})
    card_b = await _post(
        client, "/api/v1/cards", {"customer_id": b, "column_id": col_b["id"], "title": "b"}
    )
    item_a = await _post(client, "/api/v1/inbox", {"customer_id": a, "title": "a"})
    item_b = await _post(client, "/api/v1/inbox", {"customer_id": b, "title": "b"})
    assert item_a["customer_id"] == a

    assert [i["id"] for i in (await client.get("/api/v1/inbox", headers=ha)).json()] == [
        item_a["id"]
    ]
    assert (await client.get(f"/api/v1/inbox?customer_id={b}", headers=ha)).status_code == 403

    # A cannot touch B's item (or its own: customers do not write).
    for item in (item_b, item_a):
        for method, path, body in [
            ("POST", "/api/v1/inbox", {"title": "x"}),
            ("PATCH", f"/api/v1/inbox/{item['id']}", {"title": "x"}),
            ("DELETE", f"/api/v1/inbox/{item['id']}", None),
            ("POST", f"/api/v1/inbox/{item['id']}/promote", {"column_id": col_b["id"]}),
            ("POST", f"/api/v1/inbox/{item['id']}/attach", {"card_id": card_b["id"]}),
        ]:
            r = await client.request(method, path, json=body, headers=ha)
            assert r.status_code == 403, (method, path)

    # The operator cannot push A's item into B's column or card; the item survives (rollback).
    r = await client.post(
        f"/api/v1/inbox/{item_a['id']}/promote", json={"column_id": col_b["id"]}, headers=OP
    )
    assert r.status_code == 404
    r = await client.post(
        f"/api/v1/inbox/{item_a['id']}/attach", json={"card_id": card_b["id"]}, headers=OP
    )
    assert r.status_code == 404
    assert [i["id"] for i in (await client.get("/api/v1/inbox", headers=ha)).json()] == [
        item_a["id"]
    ]
    assert [i["id"] for i in (await client.get("/api/v1/inbox", headers=hb)).json()] == [
        item_b["id"]
    ]

    # Operator sees both and can promote within a customer.
    all_ids = {i["id"] for i in (await client.get("/api/v1/inbox", headers=OP)).json()}
    assert {item_a["id"], item_b["id"]} <= all_ids
    r = await client.post(
        f"/api/v1/inbox/{item_b['id']}/promote", json={"column_id": col_b["id"]}, headers=OP
    )
    assert r.status_code == 201
    assert r.json()["customer_id"] == b
