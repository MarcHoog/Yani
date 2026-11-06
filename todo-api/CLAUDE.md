# todo-api

Becomes the requests service (customer requests from forms, worked by operators on the board; see `docs\architecture.md` section 6). Today it is the todo board from the earlier personal-board phase. Postgres holds the kanban board: columns and cards as data rows, ULIDs, bodies as JSONB. Columns are rows, not an enum. Next to the board sits the inbox: flat capture items (title + body) that get promoted to a card or attached to one.

## Stack

Python 3.13, FastAPI, asyncpg, strict Pydantic, `yani-shared` (auth), uv (workspace member of repo root), ruff, pytest.

## Run

From repo root: `python dev.py up` starts postgres + todo-api via compose. Docs: http://localhost:8010/docs
Local without compose: `uv sync` at root, then from `todo-api\`: `uv run uvicorn todo_api.main:app --reload --port 8010`. Needs postgres on localhost:5432 and the `AUTH_*` env (Zitadel issuer, project ID and operator org ID from `python dev.py seed`), see `.env.example`.

| command (from `todo-api\`) | does |
|---|---|
| `uv run pytest` | tests; isolation tests skip without `TEST_DATABASE_URL` |
| `python dev.py test` (repo root) | all tests, starts neo4j + postgres and sets `TEST_*` |
| `uv run ruff check . && uv run ruff format --check .` | lint |

## Layout

```
src\todo_api\main.py            app, lifespan (create pool, schema), /health, /ready
src\todo_api\config.py          Settings (DATABASE_URL), auth_settings (AUTH_ISSUER, AUTH_AUDIENCE, AUTH_OPERATOR_ORG)
src\todo_api\auth.py            auth dependency, CallerDep
src\todo_api\database.py        SCHEMA ddl, pool, ConnDep (jsonb codec on every connection)
src\todo_api\exceptions.py      NotFound
src\todo_api\board\schemas.py   Pydantic in/out
src\todo_api\board\service.py   SQL
src\todo_api\board\router.py    /api/v1/board, /columns, /columns/{id}, /cards, /cards/{id}
src\todo_api\inbox\*            /api/v1/inbox, /inbox/{id}, /inbox/{id}/promote, /inbox/{id}/attach
tests\                          httpx ASGITransport, no lifespan. conftest: FakeIssuer (no Zitadel), `customers` fixture on real postgres
```

## Rules

- Structured fields are columns; free-form text/comments/bodies go in the `body` JSONB.
- SQL only in `service.py`, always parameterized.
- Card move = PATCH with `column_id`; without an explicit `position` the card appends to the end of the target column.
- Inbox items are not cards. `promote` turns one into a new card in a column (title and body copied), `attach` folds one into an existing card: the title becomes a `body.todos` entry, a non-empty `body.description` becomes a `body.comments` entry. Both delete the item in the same transaction. This is the only place the API knows the card body shape (`todos: [{id, text, done}]`, `comments: [{id, text, at}]`), mirrored in `portal\src\board\cardBody.ts`.
- Schema is created idempotently in lifespan (`CREATE TABLE IF NOT EXISTS`). No migrations tool yet; a breaking change needs one first.
- Errors raised only at boundary (router/service via HTTPException subclasses).
- Auth (`docs\architecture.md` section 2, details in `shared\CLAUDE.md`): every `/api/v1` route requires a valid token via the router-level dependency in `main.py`. `/health`, `/ready`, `/docs` are open and hold no customer data. No bypass flags, no "dev without auth".
- Caller (role, customer_id) comes from the Zitadel token alone; `customer_id` is the customer's Zitadel organization ID.
- `customer_id` is NOT NULL on columns, cards and inbox items. Every service function takes `scope` (`caller.scope()`: a customer_id, or None = all for operators) and filters on it; another customer's row is 404, never 403. Every route is operator only (`caller.require_operator()`), reads included: the board is the operator's work view, customers only ever see request state (customer reads arrive with requests, roadmap slice 5). Operators read everything or filter with `?customer_id=`. Creates take `caller.owner(payload.customer_id)`, so operators must pass `customer_id`.
- Rows never cross customers: a card's column, a move target, a promote target column and an attach target card must belong to the same customer, for operators too. The database enforces it for cards too: `cards (column_id, customer_id)` references `board_columns (id, customer_id)`.
- `GET /board` reads columns and cards in one repeatable-read snapshot.
- Columns are per customer and no longer seeded at startup.
- `customer_id` was added to existing tables with `ALTER TABLE ... NOT NULL`: an old dev volume with rows fails at startup. Reset with `python dev.py down -v`.
