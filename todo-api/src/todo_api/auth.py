"""Caller dependency for todo-api. Customer mapping is the customer_tenants table, owned here."""

from typing import Annotated

from fastapi import Depends, Request

from todo_api.config import auth_settings
from yani_shared.auth import Auth, Caller


async def resolve_customer(request: Request, tenant_id: str, _token: str) -> str | None:
    async with request.app.state.pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT customer_id FROM customer_tenants WHERE tenant_id = $1", tenant_id
        )


auth = Auth(auth_settings, resolve_customer)
CallerDep = Annotated[Caller, Depends(auth)]
