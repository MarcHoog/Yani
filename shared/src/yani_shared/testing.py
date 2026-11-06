"""Test-only helpers: an RSA key, an OIDC issuer served over real HTTP on localhost (discovery
document + JWKS), and a minter for Zitadel-shaped access tokens.

Services set AUTH_ISSUER to `FakeIssuer.issuer`, so the production validation path runs
unchanged and no Zitadel is needed. Never imported by service code.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from yani_shared.auth import roles_claim

PROJECT_ID = "300000000000000001"
OPERATOR_ORG_ID = "300000000000000002"


class FakeIssuer:
    def __init__(self, kid: str = "test-key") -> None:
        self.kid = kid
        self._key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(RSAAlgorithm.to_jwk(self._key.public_key()))
        jwks = json.dumps({"keys": [jwk | {"kid": kid, "use": "sig", "alg": "RS256"}]}).encode()
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
        self.issuer = f"http://127.0.0.1:{self._server.server_address[1]}"
        discovery = json.dumps(
            {"issuer": self.issuer, "jwks_uri": f"{self.issuer}/oauth/v2/keys"}
        ).encode()
        routes = {"/.well-known/openid-configuration": discovery, "/oauth/v2/keys": jwks}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                body = routes.get(self.path)
                self.send_response(200 if body else 404)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body or b"")))
                self.end_headers()
                self.wfile.write(body or b"")

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                pass

        self._server.RequestHandlerClass = Handler
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def env(self) -> dict[str, str]:
        return {"AUTH_ISSUER": self.issuer, "AUTH_AUDIENCE": PROJECT_ID}

    def token(
        self,
        roles: dict[str, dict[str, str]] | None,
        *,
        sub: str = "user-1",
        audience: str = PROJECT_ID,
        issuer: str | None = None,
        expires_in: int = 300,
    ) -> str:
        """`roles` is the Zitadel role claim value, e.g. {"customer": {"<org id>": "<domain>"}}."""
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": issuer or self.issuer,
            "aud": [audience, "client-id-of-portal"],
            "sub": sub,
            "iat": now,
            "nbf": now,
            "exp": now + expires_in,
        }
        if roles is not None:
            claims[roles_claim(PROJECT_ID)] = roles
        return jwt.encode(claims, self._key, algorithm="RS256", headers={"kid": self.kid})

    def operator_headers(self, **kwargs: Any) -> dict[str, str]:
        roles = {"operator": {OPERATOR_ORG_ID: "yani-operators.zitadel.localhost"}}
        return {"Authorization": f"Bearer {self.token(roles, **kwargs)}"}

    def customer_headers(self, customer_id: str, **kwargs: Any) -> dict[str, str]:
        roles = {"customer": {customer_id: f"{customer_id}.zitadel.localhost"}}
        return {"Authorization": f"Bearer {self.token(roles, **kwargs)}"}
