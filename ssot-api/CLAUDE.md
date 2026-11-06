# ssot-api

Inventory service: the synced model of each customer tenant (users, groups, mailboxes, devices, license SKUs and how they relate; see `docs\architecture.md` section 4). Neo4j nodes = stable ULID + label + name + `customer_id`. Relationships only. No detail payloads. The catalog is still the earlier MSP starter set; the tenant model replaces it in roadmap slice 2.

## Stack

Python 3.13, FastAPI, neo4j async driver, strict Pydantic, `yani-shared` (auth), uv (workspace member of repo root), ruff, pytest.

## Run

From repo root: `python dev.py up` starts neo4j + ssot-api via compose. Docs: http://localhost:8000/docs
Local without compose: `uv sync` at root, then from `ssot-api\`: `uv run uvicorn ssot_api.main:app --reload`. Needs neo4j on bolt://localhost:7687 and the `AUTH_*` env (Zitadel issuer, project ID and operator org ID from `python dev.py seed`), see `.env.example`.

| command (from `ssot-api\`) | does |
|---|---|
| `uv run pytest` | tests; isolation tests skip without `TEST_NEO4J_URI` |
| `python dev.py test` (repo root) | all tests, starts neo4j + postgres and sets `TEST_*` |
| `uv run ruff check . && uv run ruff format --check .` | lint |

## Layout

```
src\ssot_api\main.py            app, lifespan (refuses nodes without customer_id; unique id constraint + customer_id index per label), /health, /ready
src\ssot_api\config.py          Settings (NEO4J_*), auth_settings (AUTH_ISSUER, AUTH_AUDIENCE, AUTH_OPERATOR_ORG)
src\ssot_api\auth.py            auth dependency, CallerDep
src\ssot_api\database.py        driver, SessionDep, run()
src\ssot_api\exceptions.py      NotFound, InvalidRelation
src\ssot_api\graph\catalog.py   LABELS, RELATION_CATALOG. Only place that defines the model
src\ssot_api\graph\schemas.py   Pydantic in/out
src\ssot_api\graph\service.py   Cypher
src\ssot_api\graph\router.py    /api/v1/catalog, /nodes, /nodes/{id}, /nodes/{id}/relations, /relations
tests\                          httpx ASGITransport, no lifespan. conftest: FakeIssuer (no Zitadel), `customers` fixture on real neo4j
```

## Rules

- New label or edge: add to `catalog.py` only. Schemas and validation derive from it.
- Node props stay: id, customer_id, name, created_at, updated_at. Anything else belongs in another store keyed by id.
- Cypher only in `service.py`. Labels and relation types are interpolated from the catalog, never from raw input.
- Errors raised only at boundary (router/service via HTTPException subclasses).
- Auth (`docs\architecture.md` section 2, details in `shared\CLAUDE.md`): every `/api/v1` route requires a valid token via the router-level dependency in `main.py`. `/health`, `/ready`, `/docs` are open and hold no customer data. No bypass flags, no "dev without auth".
- Caller (role, customer_id) comes from the Zitadel token alone; no lookup in another service.
- Reads are scoped with `caller.scope()`: every Cypher read filters `n.customer_id` (and the related node's) unless the operator asked for all. Another customer's node is 404, never 403.
- Writes (nodes, relations) are operator only (`caller.require_operator()`): customers read inventory, they never change it. Operators must pass `customer_id` on create. Relations never cross customers.
- Startup refuses to run while nodes without `customer_id` exist (pre-scoping dev data). Reset with `python dev.py down -v`.
