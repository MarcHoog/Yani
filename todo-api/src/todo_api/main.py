from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI

from todo_api.auth import CallerDep, auth
from todo_api.board.router import router as board_router
from todo_api.database import create_pool
from todo_api.inbox.router import router as inbox_router
from yani_shared.auth import Caller


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = await create_pool()
    app.state.pool = pool
    yield
    await pool.close()


app = FastAPI(title="yani todo-api", version="0.1.0", lifespan=lifespan)

# Every /api/v1 route requires a valid token, including ones added later.
api = APIRouter(prefix="/api/v1", dependencies=[Depends(auth)])


@api.get("/me", tags=["auth"])
async def me(caller: CallerDep) -> Caller:
    """The caller as this service sees it. ssot-api resolves customer tokens through this."""
    return caller


api.include_router(board_router)
api.include_router(inbox_router)
app.include_router(api)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
async def ready() -> dict[str, str]:
    async with app.state.pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok", "postgres": "ok"}
