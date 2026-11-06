"""Test-only helpers: an RSA key, a JWKS served over real HTTP on localhost, a token minter.

Services point AUTH_JWKS_URL at `FakeIssuer.jwks_url` in their tests, so the production
validation path runs unchanged. Never imported by service code.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

ISSUER_TEMPLATE = "https://login.test/{tid}/v2.0"
AUDIENCE = "api://yani-test"


class FakeIssuer:
    def __init__(self, kid: str = "test-key") -> None:
        self.kid = kid
        self._key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(RSAAlgorithm.to_jwk(self._key.public_key()))
        body = json.dumps({"keys": [jwk | {"kid": kid, "use": "sig", "alg": "RS256"}]}).encode()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self.jwks_url = f"http://127.0.0.1:{self._server.server_address[1]}/keys"

    def env(self, operator_tenant_id: str, operator_object_ids: list[str]) -> dict[str, str]:
        return {
            "AUTH_ISSUER": ISSUER_TEMPLATE,
            "AUTH_JWKS_URL": self.jwks_url,
            "AUTH_AUDIENCE": AUDIENCE,
            "AUTH_OPERATOR_TENANT_ID": operator_tenant_id,
            "AUTH_OPERATOR_OBJECT_IDS": ",".join(operator_object_ids),
        }

    def token(
        self,
        tid: str,
        oid: str,
        *,
        audience: str = AUDIENCE,
        issuer: str | None = None,
        expires_in: int = 300,
    ) -> str:
        now = int(time.time())
        claims = {
            "iss": issuer or ISSUER_TEMPLATE.replace("{tid}", tid),
            "aud": audience,
            "tid": tid,
            "oid": oid,
            "iat": now,
            "nbf": now,
            "exp": now + expires_in,
        }
        return jwt.encode(claims, self._key, algorithm="RS256", headers={"kid": self.kid})

    def headers(self, tid: str, oid: str, **kwargs: Any) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token(tid, oid, **kwargs)}"}
