"""Auth env from a FakeIssuer (real JWKS over localhost HTTP) is set before the app is imported.

DB-backed tests need TEST_DATABASE_URL (`python dev.py test` sets it). They create customers
with unique ids and delete everything of those customers afterwards, so the dev database is safe.
"""

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient
from ulid import ULID

from yani_shared.testing import FakeIssuer

OPERATOR_TID = "operator-tenant"
OPERATOR_OID = "operator-user"

issuer = FakeIssuer()
os.environ.update(issuer.env(OPERATOR_TID, [OPERATOR_OID]))
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from todo_api.database import create_pool  # noqa: E402
from todo_api.main import app  # noqa: E402


def operator_headers() -> dict[str, str]:
    return issuer.headers(OPERATOR_TID, OPERATOR_OID)


@dataclass
class Customer:
    customer_id: str
    tenant_id: str

    @property
    def headers(self) -> dict[str, str]:
        return issuer.headers(self.tenant_id, "some-user")


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


@pytest.fixture
async def customers() -> AsyncIterator[tuple[Customer, Customer]]:
    """Two mapped customers, A and B, on a real database."""
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL not set (python dev.py test sets it)")
    pool = await create_pool()
    app.state.pool = pool
    a = Customer(f"test-{ULID()}", f"tid-{ULID()}")
    b = Customer(f"test-{ULID()}", f"tid-{ULID()}")
    ids = [a.customer_id, b.customer_id]
    async with pool.acquire() as conn:
        for c in (a, b):
            await conn.execute(
                "INSERT INTO customer_tenants (tenant_id, customer_id) VALUES ($1, $2)",
                c.tenant_id,
                c.customer_id,
            )
    try:
        yield a, b
    finally:
        async with pool.acquire() as conn:
            for table in ("cards", "inbox_items", "board_columns", "customer_tenants"):
                await conn.execute(f"DELETE FROM {table} WHERE customer_id = ANY($1)", ids)
        await pool.close()
        del app.state.pool
