"""JWT validation via the issuer's JWKS, and the caller dependency. docs/architecture.md section 2.

The issuer is yani's Zitadel. Tokens are Zitadel JWT access tokens for the `yani` project
(audience = project ID). Role and customer come from Zitadel's project role claim:

    "urn:zitadel:iam:org:project:<project id>:roles": {"customer": {"<org id>": "<org domain>"}}

- `operator` role: an operator, only when the claim maps it to the operator organization
  (AUTH_OPERATOR_ORG). Zitadel setup already keeps `operator` out of customer project grants;
  this check holds even if a grant is ever misconfigured.
- `customer` role: a customer user. customer_id is the organization ID in the claim, which is the
  customer's own Zitadel organization (customer orgs only get `customer` via a project grant).

Every API builds one `Auth` and depends on it for every `/api/v1` route. There is no way to turn
validation off.
"""

import asyncio
import math
import time
from typing import Annotated, Any, Literal

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ALGORITHMS = ["RS256"]
REQUIRED_CLAIMS = ["exp", "iss", "aud", "sub"]
ROLES = ("operator", "customer")


def roles_claim(project_id: str) -> str:
    return f"urn:zitadel:iam:org:project:{project_id}:roles"


class AuthSettings(BaseSettings):
    """AUTH_* env. Both required: a service without them does not start."""

    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=".env", extra="ignore")

    # Zitadel issuer, e.g. http://zitadel.localhost:8081. Signing keys are found via
    # <issuer>/.well-known/openid-configuration.
    issuer: str = Field(min_length=1)
    # ID of the `yani` project in Zitadel. Written to .env by `python dev.py seed`.
    audience: str = Field(min_length=1)
    # ID of the operator organization in Zitadel. Written to .env by `python dev.py seed`.
    operator_org: str = Field(min_length=1)


class Unauthorized(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
        )


class Forbidden(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class Caller(BaseModel):
    """Who is calling. Operators have no customer_id; customers always have one."""

    model_config = ConfigDict(frozen=True)

    role: Literal["operator", "customer"]
    subject: str
    customer_id: str | None

    @property
    def is_operator(self) -> bool:
        return self.role == "operator"

    def require_operator(self) -> None:
        if not self.is_operator:
            raise Forbidden("Operator only")

    def scope(self, customer_id: str | None = None) -> str | None:
        """Customer filter for a read. None means all customers (operator only).

        Operator: the filter they asked for. Customer: always their own; asking for another
        customer is refused, never silently honoured.
        """
        if self.is_operator:
            return customer_id
        if customer_id is not None and customer_id != self.customer_id:
            raise Forbidden("Not your customer")
        return self.customer_id

    def owner(self, customer_id: str | None) -> str:
        """customer_id for a new row. Operators must name it; customers get their own."""
        if self.is_operator:
            if not customer_id:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_CONTENT,
                    "customer_id is required for operator tokens",
                )
            return customer_id
        if customer_id is not None and customer_id != self.customer_id:
            raise Forbidden("Not your customer")
        return str(self.customer_id)


def caller_from_claims(claims: dict[str, Any], project_id: str, operator_org: str) -> Caller:
    """Maps validated claims to a Caller. Anything unclear is refused (403), never guessed."""
    granted = claims.get(roles_claim(project_id))
    if not isinstance(granted, dict):
        raise Forbidden("No yani role")
    roles = [role for role in ROLES if isinstance(granted.get(role), dict)]
    if len(roles) != 1:
        raise Forbidden("No yani role" if not roles else "Ambiguous yani role")
    subject = str(claims["sub"])
    if roles[0] == "operator":
        if list(granted["operator"]) != [operator_org]:
            raise Forbidden("Operator role must come from the operator organization")
        return Caller(role="operator", subject=subject, customer_id=None)
    orgs = list(granted["customer"])
    if operator_org in orgs:
        raise Forbidden("Customer role cannot come from the operator organization")
    if len(orgs) != 1 or not isinstance(orgs[0], str) or not orgs[0]:
        raise Forbidden("Customer role must come from exactly one organization")
    return Caller(role="customer", subject=subject, customer_id=orgs[0])


def _unavailable(exc: Exception | None = None) -> HTTPException:
    error = HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Signing keys unavailable")
    error.__cause__ = exc
    return error


class JwksCache:
    """Signing keys by kid, found via the issuer's OIDC discovery document. Refetches when a kid
    is unknown, at most once per interval, failed attempts included. Keys it cannot use are
    skipped."""

    def __init__(self, issuer: str, min_refresh_seconds: float = 60) -> None:
        self._discovery_url = issuer.rstrip("/") + "/.well-known/openid-configuration"
        self._jwks_url: str | None = None
        self._min_refresh = min_refresh_seconds
        self._keys: dict[str, Any] = {}
        self._fetched_at = -math.inf
        self._lock = asyncio.Lock()

    async def get(self, kid: str) -> Any | None:
        if kid not in self._keys:
            async with self._lock:
                if (
                    kid not in self._keys
                    and time.monotonic() - self._fetched_at >= self._min_refresh
                ):
                    await self._refresh()
        return self._keys.get(kid)

    async def _refresh(self) -> None:
        # Counted as an attempt up front, so a failing issuer is not hit on every request.
        self._fetched_at = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if self._jwks_url is None:
                    discovery = await _get_json(client, self._discovery_url)
                    jwks_uri = discovery.get("jwks_uri")
                    if not isinstance(jwks_uri, str):
                        raise _unavailable()
                    self._jwks_url = jwks_uri
                jwks = await _get_json(client, self._jwks_url)
        except (httpx.HTTPError, ValueError) as exc:
            raise _unavailable(exc) from exc
        keys: dict[str, Any] = {}
        entries = jwks.get("keys")
        for jwk in entries if isinstance(entries, list) else []:
            if not isinstance(jwk, dict) or jwk.get("kty") != "RSA" or not jwk.get("kid"):
                continue
            if jwk.get("use", "sig") != "sig":
                continue
            try:
                keys[jwk["kid"]] = jwt.PyJWK(jwk, algorithm="RS256").key
            except jwt.PyJWTError:
                continue
        self._keys = keys


async def _get_json(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    response = await client.get(url)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError(f"{url} did not return a JSON object")
    return body


_bearer = HTTPBearer(auto_error=False)


class Auth:
    """FastAPI dependency: validates the bearer token and returns the Caller."""

    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings
        self._keys = JwksCache(settings.issuer)

    async def __call__(
        self, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
    ) -> Caller:
        if credentials is None:
            raise Unauthorized("Missing bearer token")
        claims = await self.validate(credentials.credentials)
        return caller_from_claims(claims, self._settings.audience, self._settings.operator_org)

    async def validate(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise Unauthorized("Malformed token") from exc
        kid = header.get("kid")
        key = await self._keys.get(kid) if isinstance(kid, str) else None
        if key is None:
            raise Unauthorized("Unknown signing key")
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                key,
                algorithms=ALGORITHMS,
                audience=self._settings.audience,
                issuer=self._settings.issuer,
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as exc:
            raise Unauthorized("Invalid token") from exc
        return claims
