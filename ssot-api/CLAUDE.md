# ssot-api

Graph SSOT service. Neo4j nodes = stable ULID + label + name. Relationships only. No detail payloads.

## Stack

Python 3.13, FastAPI, neo4j async driver, strict Pydantic, uv (workspace member of repo root), ruff, pytest.

## Run

From repo root: `.\dev.ps1 up` starts neo4j + ssot-api via compose. Docs: http://localhost:8000/docs
Local without compose: `uv sync` at root, then from `ssot-api\`: `uv run uvicorn ssot_api.main:app --reload`. Needs neo4j on bolt://localhost:7687, see `.env.example`.

| command (from `ssot-api\`) | does |
|---|---|
| `uv run pytest` | tests, no neo4j needed |
| `uv run ruff check . && uv run ruff format --check .` | lint |

## Layout

```
src\ssot_api\main.py            app, lifespan (unique id constraint per label), /health, /ready
src\ssot_api\config.py          Settings, NEO4J_* env
src\ssot_api\database.py        driver, SessionDep, run()
src\ssot_api\exceptions.py      NotFound, InvalidRelation
src\ssot_api\graph\catalog.py   LABELS, RELATION_CATALOG. Only place that defines the model
src\ssot_api\graph\schemas.py   Pydantic in/out
src\ssot_api\graph\service.py   Cypher
src\ssot_api\graph\router.py    /api/v1/catalog, /nodes, /nodes/{id}, /nodes/{id}/relations, /relations
tests\                          httpx ASGITransport, no lifespan, no db
```

## Rules

- New label or edge: add to `catalog.py` only. Schemas and validation derive from it.
- Node props stay: id, name, created_at, updated_at. Anything else belongs in another store keyed by id.
- Cypher only in `service.py`. Labels and relation types are interpolated from the catalog, never from raw input.
- Errors raised only at boundary (router/service via HTTPException subclasses).
- No auth yet. JWT via Zitadel JWKS comes with the shared python package. Do not add bypass flags.
