"""Auth env from a FakeIssuer (real JWKS over localhost HTTP) is set before the app is imported.

Customer tokens are resolved through todo-api's /api/v1/me; here a stand-in for that endpoint is
served over localhost HTTP from the `TENANTS` mapping, so the real resolver path runs.

DB-backed tests need TEST_NEO4J_URI (+ TEST_NEO4J_USER / TEST_NEO4J_PASSWORD); `python dev.py
test` sets them. They create customers with unique ids and detach-delete those afterwards.
"""

import json
import os
import threading
from collections.abc import AsyncIterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from neo4j import AsyncGraphDatabase
from ulid import ULID

from yani_shared.testing import FakeIssuer

OPERATOR_TID = "operator-tenant"
OPERATOR_OID = "operator-user"

# tenant_id -> customer_id, as todo-api's customer_tenants table would hold it.
TENANTS: dict[str, str] = {}


class _FakeTodoApi(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        tid = jwt.decode(token, options={"verify_signature": False})["tid"]
        if self.path != "/api/v1/me" or tid not in TENANTS:
            self.send_response(403)
            self.end_headers()
            return
        body = json.dumps({"role": "customer", "customer_id": TENANTS[tid]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


_todo = ThreadingHTTPServer(("127.0.0.1", 0), _FakeTodoApi)
threading.Thread(target=_todo.serve_forever, daemon=True).start()

issuer = FakeIssuer()
os.environ.update(issuer.env(OPERATOR_TID, [OPERATOR_OID]))
os.environ["TODO_API_URL"] = f"http://127.0.0.1:{_todo.server_address[1]}"

from ssot_api import database  # noqa: E402
from ssot_api.main import app  # noqa: E402


def operator_headers() -> dict[str, str]:
    return issuer.headers(OPERATOR_TID, OPERATOR_OID)


@dataclass
class Customer:
    customer_id: str
    tenant_id: str

    @property
    def headers(self) -> dict[str, str]:
        return issuer.headers(self.tenant_id, "some-user")


def new_customer() -> Customer:
    customer = Customer(f"test-{ULID()}", f"tid-{ULID()}")
    TENANTS[customer.tenant_id] = customer.customer_id
    return customer


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


@pytest.fixture
async def customers() -> AsyncIterator[tuple[Customer, Customer]]:
    """Two mapped customers, A and B, on a real Neo4j."""
    uri = os.environ.get("TEST_NEO4J_URI")
    if not uri:
        pytest.skip("TEST_NEO4J_URI not set (python dev.py test sets it)")
    auth = (os.environ.get("TEST_NEO4J_USER", "neo4j"), os.environ.get("TEST_NEO4J_PASSWORD", ""))
    # A driver per test: the async driver is bound to the event loop it first runs on.
    original, database.driver = database.driver, AsyncGraphDatabase.driver(uri, auth=auth)
    a, b = new_customer(), new_customer()
    try:
        yield a, b
    finally:
        async with database.driver.session() as session:
            await session.run(
                "MATCH (n) WHERE n.customer_id IN $ids DETACH DELETE n",
                ids=[a.customer_id, b.customer_id],
            )
        await database.driver.close()
        database.driver = original
