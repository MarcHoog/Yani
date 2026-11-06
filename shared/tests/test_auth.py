from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from httpx import ASGITransport, AsyncClient

from yani_shared.auth import Auth, AuthSettings, Caller
from yani_shared.testing import FakeIssuer

OPERATOR_TID = "op-tenant"
OPERATOR_OID = "op-user"
CUSTOMER_TID = "customer-tenant"

issuer = FakeIssuer()
settings = AuthSettings.model_validate(
    {
        "issuer": "https://login.test/{tid}/v2.0",
        "jwks_url": issuer.jwks_url,
        "audience": "api://yani-test",
        "operator_tenant_id": OPERATOR_TID,
        "operator_object_ids": f"{OPERATOR_OID}, other-op",
    }
)


async def resolve(_request: Request, tenant_id: str, _token: str) -> str | None:
    return {CUSTOMER_TID: "cust-a"}.get(tenant_id)


auth = Auth(settings, resolve)
app = FastAPI()


@app.get("/me")
async def me(caller: Annotated[Caller, Depends(auth)]) -> Caller:
    return caller


async def get(headers: dict[str, str] | None = None) -> tuple[int, dict]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/me", headers=headers or {})
    return r.status_code, r.json()


def test_operator_object_ids_split_from_env_string() -> None:
    assert settings.operator_object_ids == [OPERATOR_OID, "other-op"]


async def test_no_token_is_401() -> None:
    code, _ = await get()
    assert code == 401


async def test_garbage_token_is_401() -> None:
    code, _ = await get({"Authorization": "Bearer not-a-jwt"})
    assert code == 401


async def test_wrong_audience_is_401() -> None:
    code, _ = await get(issuer.headers(CUSTOMER_TID, "u1", audience="api://someone-else"))
    assert code == 401


async def test_wrong_issuer_is_401() -> None:
    code, _ = await get(issuer.headers(CUSTOMER_TID, "u1", issuer="https://evil.test/x/v2.0"))
    assert code == 401


async def test_expired_token_is_401() -> None:
    code, _ = await get(issuer.headers(CUSTOMER_TID, "u1", expires_in=-60))
    assert code == 401


async def test_token_signed_by_other_key_is_401() -> None:
    code, _ = await get(FakeIssuer().headers(CUSTOMER_TID, "u1"))
    assert code == 401


async def test_operator_on_allow_list() -> None:
    code, body = await get(issuer.headers(OPERATOR_TID, OPERATOR_OID))
    assert code == 200
    assert body["role"] == "operator"
    assert body["customer_id"] is None


async def test_operator_tenant_account_not_on_allow_list_is_403() -> None:
    code, _ = await get(issuer.headers(OPERATOR_TID, "random-user"))
    assert code == 403


async def test_customer_tenant_maps_to_customer_id() -> None:
    code, body = await get(issuer.headers(CUSTOMER_TID, "u1"))
    assert code == 200
    assert body["role"] == "customer"
    assert body["customer_id"] == "cust-a"


async def test_unknown_tenant_is_403() -> None:
    code, _ = await get(issuer.headers("stranger", "u1"))
    assert code == 403


def test_customer_scope_is_always_own() -> None:
    caller = Caller(role="customer", tenant_id="t", object_id="o", customer_id="a")
    assert caller.scope() == "a"
    assert caller.scope("a") == "a"
    assert caller.owner(None) == "a"
    with pytest.raises(HTTPException) as exc:
        caller.scope("b")
    assert exc.value.status_code == 403
    with pytest.raises(HTTPException):
        caller.owner("b")
    with pytest.raises(HTTPException):
        caller.require_operator()


def test_operator_scope_and_owner() -> None:
    caller = Caller(role="operator", tenant_id="t", object_id="o", customer_id=None)
    assert caller.scope() is None
    assert caller.scope("b") == "b"
    assert caller.owner("b") == "b"
    with pytest.raises(HTTPException) as exc:
        caller.owner(None)
    assert exc.value.status_code == 422
    caller.require_operator()
