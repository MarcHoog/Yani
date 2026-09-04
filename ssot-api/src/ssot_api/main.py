from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

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
    yield
    await driver.close()


app = FastAPI(title="yani ssot-api", version="0.1.0", lifespan=lifespan)

api = APIRouter(prefix="/api/v1")
api.include_router(graph_router)
app.include_router(api)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
async def ready() -> dict[str, str]:
    await driver.verify_connectivity()
    return {"status": "ok", "neo4j": "ok"}
