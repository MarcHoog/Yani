from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from todo_api.board import service
from todo_api.board.router import router as board_router
from todo_api.database import create_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = await create_pool()
    async with pool.acquire() as conn:
        await service.seed_columns(conn)
    app.state.pool = pool
    yield
    await pool.close()


app = FastAPI(title="yani todo-api", version="0.1.0", lifespan=lifespan)

api = APIRouter(prefix="/api/v1")
api.include_router(board_router)
app.include_router(api)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
async def ready() -> dict[str, str]:
    async with app.state.pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok", "postgres": "ok"}
