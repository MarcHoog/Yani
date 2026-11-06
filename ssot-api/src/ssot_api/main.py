from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI

from ssot_api.auth import auth
from ssot_api.database import driver
from ssot_api.graph.catalog import LABELS
from ssot_api.graph.router import router as graph_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    async with driver.session() as session:
        for label in LABELS:
            await session.run(
                f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
            await session.run(
                f"CREATE INDEX {label.lower()}_customer IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.customer_id)"
            )
    yield
    await driver.close()


app = FastAPI(title="yani ssot-api", version="0.1.0", lifespan=lifespan)

# Every /api/v1 route requires a valid token, including ones added later.
api = APIRouter(prefix="/api/v1", dependencies=[Depends(auth)])
api.include_router(graph_router)
app.include_router(api)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
async def ready() -> dict[str, str]:
    await driver.verify_connectivity()
    return {"status": "ok", "neo4j": "ok"}
