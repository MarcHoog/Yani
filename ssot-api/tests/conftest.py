"""Auth env from a FakeIssuer (real discovery + JWKS over localhost HTTP) is set before the app
is imported. No Zitadel needed.

DB-backed tests need TEST_NEO4J_URI (+ TEST_NEO4J_USER / TEST_NEO4J_PASSWORD); `python dev.py
test` sets them. They use customer ids unique to the test and detach-delete those afterwards.
"""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from neo4j import AsyncGraphDatabase
from ulid import ULID

from yani_shared.testing import FakeIssuer

issuer = FakeIssuer()
os.environ.update(issuer.env())

from ssot_api import database  # noqa: E402
from ssot_api.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


@pytest.fixture
async def customers() -> AsyncIterator[tuple[str, str]]:
    """Two customer ids, A and B, on a real Neo4j."""
    uri = os.environ.get("TEST_NEO4J_URI")
    if not uri:
        pytest.skip("TEST_NEO4J_URI not set (python dev.py test sets it)")
    auth = (os.environ.get("TEST_NEO4J_USER", "neo4j"), os.environ.get("TEST_NEO4J_PASSWORD", ""))
    # A driver per test: the async driver is bound to the event loop it first runs on.
    original, database.driver = database.driver, AsyncGraphDatabase.driver(uri, auth=auth)
    ids = (f"test-{ULID()}", f"test-{ULID()}")
    try:
        yield ids
    finally:
        async with database.driver.session() as session:
            await session.run(
                "MATCH (n) WHERE n.customer_id IN $ids DETACH DELETE n", ids=list(ids)
            )
        await database.driver.close()
        database.driver = original
