from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from ssot_api.config import settings

driver: AsyncDriver = AsyncGraphDatabase.driver(
    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with driver.session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def run(session: AsyncSession, query: str, **params: Any) -> list[dict[str, Any]]:
    result = await session.run(query, **params)
    return [record.data() for record in await result.fetch(10_000)]
