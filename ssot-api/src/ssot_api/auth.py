"""Caller dependency for ssot-api.

The tenant -> customer mapping is owned by todo-api. A customer token is resolved by calling
todo-api's /api/v1/me with the caller's own (already validated) token, so ssot-api needs no
service credentials and no Postgres access. Hits are cached per tenant ID for a few minutes.
"""

import time
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status

from ssot_api.config import auth_settings, settings
from yani_shared.auth import Auth, Caller, Unauthorized

_customers: dict[str, tuple[str, float]] = {}


async def resolve_customer(_request: Request, tenant_id: str, token: str) -> str | None:
    hit = _customers.get(tenant_id)
    if hit and hit[1] > time.monotonic():
        return hit[0]
    try:
        async with httpx.AsyncClient(base_url=settings.todo_api_url, timeout=10) as client:
            response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Customer lookup unavailable"
        ) from exc
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise Unauthorized("Token rejected")
    if response.status_code == status.HTTP_403_FORBIDDEN:
        return None
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Customer lookup failed")
    customer_id = response.json().get("customer_id")
    if not isinstance(customer_id, str):
        return None
    _customers[tenant_id] = (customer_id, time.monotonic() + settings.customer_cache_seconds)
    return customer_id


auth = Auth(auth_settings, resolve_customer)
CallerDep = Annotated[Caller, Depends(auth)]
