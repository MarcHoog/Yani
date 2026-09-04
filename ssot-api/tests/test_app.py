from httpx import ASGITransport, AsyncClient

from ssot_api.graph import catalog
from ssot_api.main import app


async def test_health() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_catalog_endpoint_matches_module() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/v1/catalog")
    assert r.status_code == 200
    assert r.json()["labels"] == catalog.LABELS


def test_catalog_only_references_known_labels() -> None:
    for a, _, b in catalog.RELATION_CATALOG:
        assert a in catalog.LABELS and b in catalog.LABELS
    assert catalog.is_allowed("Customer", "HAS_TENANT", "Tenant")
    assert not catalog.is_allowed("Tenant", "HAS_TENANT", "Customer")


async def test_create_node_rejects_unknown_label() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/nodes", json={"label": "Ticket", "name": "x"})
    assert r.status_code == 422
