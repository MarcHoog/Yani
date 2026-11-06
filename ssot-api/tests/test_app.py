from httpx import AsyncClient

from ssot_api.graph import catalog
from tests.conftest import operator_headers


async def test_health(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_catalog_endpoint_matches_module(client: AsyncClient) -> None:
    r = await client.get("/api/v1/catalog", headers=operator_headers())
    assert r.status_code == 200
    assert r.json()["labels"] == catalog.LABELS


def test_catalog_only_references_known_labels() -> None:
    for a, _, b in catalog.RELATION_CATALOG:
        assert a in catalog.LABELS and b in catalog.LABELS
    assert catalog.is_allowed("Customer", "HAS_TENANT", "Tenant")
    assert not catalog.is_allowed("Tenant", "HAS_TENANT", "Customer")


async def test_create_node_rejects_unknown_label(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/nodes",
        json={"customer_id": "c", "label": "Ticket", "name": "x"},
        headers=operator_headers(),
    )
    assert r.status_code == 422
