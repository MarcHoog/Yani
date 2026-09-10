from httpx import ASGITransport, AsyncClient

from todo_api.database import get_connection
from todo_api.main import app

app.dependency_overrides[get_connection] = lambda: None


async def test_health() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_create_card_rejects_empty_title() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/cards", json={"column_id": "x", "title": ""})
    assert r.status_code == 422


async def test_create_card_rejects_unknown_fields() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/cards", json={"column_id": "x", "title": "y", "status": "open"})
    assert r.status_code == 422


async def test_update_card_rejects_negative_position() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.patch("/api/v1/cards/some-id", json={"position": -1})
    assert r.status_code == 422


async def test_create_inbox_item_rejects_empty_title() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/inbox", json={"title": ""})
    assert r.status_code == 422


async def test_create_inbox_item_rejects_unknown_fields() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/inbox", json={"title": "x", "description": "y"})
    assert r.status_code == 422


async def test_promote_inbox_item_requires_column() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/inbox/some-id/promote", json={})
    assert r.status_code == 422


async def test_attach_inbox_item_requires_card() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/inbox/some-id/attach", json={"column_id": "x"})
    assert r.status_code == 422
