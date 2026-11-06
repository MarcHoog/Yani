"""Auth env from a FakeIssuer (real discovery + JWKS over localhost HTTP) is set before the app
is imported. No Zitadel needed.

DB-backed tests need TEST_DATABASE_URL (`python dev.py test` sets it). They use customer ids
unique to the test and delete every row of those customers afterwards, so the dev database is safe.
"""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from ulid import ULID

from yani_shared.testing import FakeIssuer

issuer = FakeIssuer()
os.environ.update(issuer.env())
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from todo_api.database import create_pool  # noqa: E402
from todo_api.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


@pytest.fixture
async def customers() -> AsyncIterator[tuple[str, str]]:
    """Two customer ids, A and B, on a real database."""
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL not set (python dev.py test sets it)")
    pool = await create_pool()
    app.state.pool = pool
    ids = (f"test-{ULID()}", f"test-{ULID()}")
    try:
        yield ids
    finally:
        async with pool.acquire() as conn:
            for table in ("cards", "inbox_items", "board_columns"):
                await conn.execute(f"DELETE FROM {table} WHERE customer_id = ANY($1)", list(ids))
        await pool.close()
        del app.state.pool
