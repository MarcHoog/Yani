# todo-api

Todo board service. Postgres holds the kanban board: columns and cards as data rows, ULIDs, bodies as JSONB. Columns are rows, not an enum.

## Stack

Python 3.13, FastAPI, asyncpg, strict Pydantic, uv (workspace member of repo root), ruff, pytest.

## Run

From repo root: `.\dev.ps1 up` starts postgres + todo-api via compose. Docs: http://localhost:8010/docs
Local without compose: `uv sync` at root, then from `todo-api\`: `uv run uvicorn todo_api.main:app --reload --port 8010`. Needs postgres on localhost:5432, see `.env.example`.

| command (from `todo-api\`) | does |
|---|---|
| `uv run pytest` | tests, no postgres needed |
| `uv run ruff check . && uv run ruff format --check .` | lint |

## Layout

```
src\todo_api\main.py            app, lifespan (create pool, schema, seed default columns), /health, /ready
src\todo_api\config.py          Settings, DATABASE_URL env
src\todo_api\database.py        SCHEMA ddl, pool, ConnDep (jsonb codec on every connection)
src\todo_api\exceptions.py      NotFound
src\todo_api\board\schemas.py   Pydantic in/out
src\todo_api\board\service.py   SQL
src\todo_api\board\router.py    /api/v1/board, /columns, /columns/{id}, /cards, /cards/{id}
tests\                          httpx ASGITransport, no lifespan, no db
```

## Rules

- Structured fields are columns; free-form text/comments/bodies go in the `body` JSONB.
- SQL only in `service.py`, always parameterized.
- Card move = PATCH with `column_id`; without an explicit `position` the card appends to the end of the target column.
- Schema is created idempotently in lifespan (`CREATE TABLE IF NOT EXISTS`). No migrations tool yet; a breaking change needs one first.
- Errors raised only at boundary (router/service via HTTPException subclasses).
- No auth, by design. Single-user local app. Do not add auth scaffolding or bypass flags.
