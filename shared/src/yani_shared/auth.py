"""JWT validation via the issuer's JWKS, and the caller dependency. docs/architecture.md section 2.

Every API builds one `Auth` with its own customer resolver and depends on it for every
`/api/v1` route. There is no way to turn validation off.
"""

import asyncio
import math
import time
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ALGORITHMS = ["RS256"]
REQUIRED_CLAIMS = ["exp", "iss", "aud", "tid", "oid"]

# (request, tenant_id, raw bearer token) -> customer_id, or None when the tenant is not a customer.
CustomerResolver = Callable[[Request, str, str], Awaitable[str | None]]


class AuthSettings(BaseSettings):
    """AUTH_* env. All required: a service without them does not start."""

    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=".env", extra="ignore")

    # Expected `iss`. `{tid}` is replaced with the token's tenant ID, which is how multi-tenant
    # Entra issuers look: https://login.microsoftonline.com/{tid}/v2.0
    issuer: str = Field(min_length=1)
    jwks_url: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    operator_tenant_id: str = Field(min_length=1)
    # Comma-separated object IDs (`oid`) of operator accounts in the operator tenant.
    operator_object_ids: Annotated[list[str], NoDecode] = Field(min_length=1)

    @field_validator("operator_object_ids", mode="before")
    @classmethod
    def _split_ids(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


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
    tenant_id: str
    object_id: str
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
        scoped = self.scope(customer_id)
        assert scoped is not None
        return scoped


class JwksCache:
    """Signing keys by kid. Refetches when a kid is unknown, at most once per interval."""

    def __init__(self, url: str, min_refresh_seconds: float = 60) -> None:
        self._url = url
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
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self._url)
                response.raise_for_status()
            jwks = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "Signing keys unavailable"
            ) from exc
        keys: dict[str, Any] = {}
        for jwk in jwks.get("keys", []):
            if jwk.get("kty") == "RSA" and jwk.get("kid") and jwk.get("use", "sig") == "sig":
                keys[jwk["kid"]] = jwt.PyJWK(jwk, algorithm="RS256").key
        self._keys = keys
        self._fetched_at = time.monotonic()


_bearer = HTTPBearer(auto_error=False)


class Auth:
    """FastAPI dependency: validates the bearer token and returns the Caller."""

    def __init__(self, settings: AuthSettings, resolve_customer: CustomerResolver) -> None:
        self._settings = settings
        self._keys = JwksCache(settings.jwks_url)
        self._resolve_customer = resolve_customer

    async def __call__(
        self,
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    ) -> Caller:
        if credentials is None:
            raise Unauthorized("Missing bearer token")
        token = credentials.credentials
        claims = await self.validate(token)
        tenant_id: str = claims["tid"]
        object_id: str = claims["oid"]

        if tenant_id == self._settings.operator_tenant_id:
            if object_id not in self._settings.operator_object_ids:
                raise Forbidden("Account is not an operator")
            return Caller(
                role="operator", tenant_id=tenant_id, object_id=object_id, customer_id=None
            )

        customer_id = await self._resolve_customer(request, tenant_id, token)
        if customer_id is None:
            raise Forbidden("Tenant is not a customer")
        return Caller(
            role="customer", tenant_id=tenant_id, object_id=object_id, customer_id=customer_id
        )

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
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as exc:
            raise Unauthorized("Invalid token") from exc
        tenant_id = claims["tid"]
        if not isinstance(tenant_id, str) or not isinstance(claims["oid"], str):
            raise Unauthorized("Invalid token")
        if claims["iss"] != self._settings.issuer.replace("{tid}", tenant_id):
            raise Unauthorized("Invalid issuer")
        return claims
