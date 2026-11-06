import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from yani_shared.auth import Auth, AuthSettings, Caller, JwksCache, caller_from_claims, roles_claim
from yani_shared.testing import OPERATOR_ORG_ID, PROJECT_ID, FakeIssuer

issuer = FakeIssuer()
auth = Auth(AuthSettings.model_validate({"issuer": issuer.issuer, "audience": PROJECT_ID}))
app = FastAPI()


@app.get("/me")
async def me(caller: Annotated[Caller, Depends(auth)]) -> Caller:
    return caller


async def get(headers: dict[str, str] | None = None) -> tuple[int, Any]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/me", headers=headers or {})
    return r.status_code, r.json()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_no_token_is_401() -> None:
    code, _ = await get()
    assert code == 401


async def test_garbage_token_is_401() -> None:
    code, _ = await get(bearer("not-a-jwt"))
    assert code == 401


async def test_wrong_audience_is_401() -> None:
    code, _ = await get(issuer.customer_headers("org-a", audience="other-project"))
    assert code == 401


async def test_wrong_issuer_is_401() -> None:
    code, _ = await get(issuer.customer_headers("org-a", issuer="http://evil.test"))
    assert code == 401


async def test_expired_token_is_401() -> None:
    code, _ = await get(issuer.customer_headers("org-a", expires_in=-60))
    assert code == 401


async def test_token_signed_by_other_key_is_401() -> None:
    other = FakeIssuer()
    roles = {"customer": {"org-a": "a"}}
    code, _ = await get(bearer(other.token(roles, issuer=issuer.issuer)))
    assert code == 401


async def test_operator() -> None:
    code, body = await get(issuer.operator_headers(sub="op-1"))
    assert code == 200
    assert body == {"role": "operator", "subject": "op-1", "customer_id": None}


async def test_customer_id_is_the_org_of_the_customer_role() -> None:
    code, body = await get(issuer.customer_headers("org-a"))
    assert code == 200
    assert body["role"] == "customer"
    assert body["customer_id"] == "org-a"


async def test_token_without_yani_role_is_403() -> None:
    code, _ = await get(bearer(issuer.token(None)))
    assert code == 403
    code, _ = await get(bearer(issuer.token({"admin": {"org-a": "a"}})))
    assert code == 403


def claims(roles: Any) -> dict[str, Any]:
    return {"sub": "u", roles_claim(PROJECT_ID): roles}


@pytest.mark.parametrize(
    "roles",
    [
        {"operator": {OPERATOR_ORG_ID: "op"}, "customer": {"org-a": "a"}},
        {"customer": {"org-a": "a", "org-b": "b"}},
        {"customer": {}},
        {"customer": "org-a"},
        ["customer"],
    ],
)
def test_unclear_roles_are_refused(roles: Any) -> None:
    with pytest.raises(HTTPException) as exc:
        caller_from_claims(claims(roles), PROJECT_ID)
    assert exc.value.status_code == 403


def test_roles_of_another_project_are_ignored() -> None:
    other = {"sub": "u", roles_claim("other-project"): {"operator": {OPERATOR_ORG_ID: "op"}}}
    with pytest.raises(HTTPException):
        caller_from_claims(other, PROJECT_ID)


def test_customer_scope_is_always_own() -> None:
    caller = Caller(role="customer", subject="s", customer_id="a")
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
    caller = Caller(role="operator", subject="s", customer_id=None)
    assert caller.scope() is None
    assert caller.scope("b") == "b"
    assert caller.owner("b") == "b"
    with pytest.raises(HTTPException) as exc:
        caller.owner(None)
    assert exc.value.status_code == 422
    caller.require_operator()


def serve(routes: dict[str, Any]) -> str:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = json.dumps(routes[self.path]).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


async def test_unusable_keys_are_skipped() -> None:
    good = json.loads(urllib.request.urlopen(issuer.issuer + "/oauth/v2/keys").read())["keys"][0]
    keys = [{"kty": "RSA", "kid": "broken", "n": "x"}, "not-a-dict", good]
    base = serve({"/k": {"keys": keys}})
    base = serve({"/.well-known/openid-configuration": {"jwks_uri": base + "/k"}})
    cache = JwksCache(base)
    assert await cache.get("broken") is None
    assert await cache.get(good["kid"]) is not None


async def test_non_object_jwks_is_503() -> None:
    base = serve({"/k": ["nope"]})
    base = serve({"/.well-known/openid-configuration": {"jwks_uri": base + "/k"}})
    with pytest.raises(HTTPException) as exc:
        await JwksCache(base).get("any")
    assert exc.value.status_code == 503
