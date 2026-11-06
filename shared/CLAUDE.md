# shared

`yani-shared` (`yani_shared`): Python code every backend uses. Today: auth (`docs\architecture.md` section 2). Later per the "Shared code" decision: settings, logging, db clients.

## Stack

Python 3.13, FastAPI, PyJWT (crypto), httpx, pydantic-settings, uv (workspace member of repo root), ruff, pytest.

## Run

Library only. Services depend on it as `yani-shared = { workspace = true }`; their Dockerfiles copy `shared\`.

| command (from `shared\`) | does |
|---|---|
| `uv run pytest` | tests, no network or db needed |
| `uv run ruff check . && uv run ruff format --check .` | lint |

## Layout

```
src\yani_shared\auth.py      AuthSettings (AUTH_* env), JwksCache, Auth dependency, Caller, Unauthorized, Forbidden
src\yani_shared\testing.py   FakeIssuer: test RSA key, JWKS over real localhost HTTP, token minter. Tests only
tests\                       Auth against a throwaway FastAPI app
```

## Auth

- `AUTH_ISSUER` (expected `iss`; `{tid}` is replaced with the token's `tid`, for multi-tenant Entra), `AUTH_JWKS_URL`, `AUTH_AUDIENCE`, `AUTH_OPERATOR_TENANT_ID`, `AUTH_OPERATOR_OBJECT_IDS` (comma-separated `oid`s). All required; a service without them does not start.
- Token: RS256 only, signature from the JWKS (refetched on an unknown `kid`, at most once a minute), `aud`, `exp`, `iss`, and `tid` + `oid` present.
- Caller: `operator` = `tid` is the operator tenant and `oid` is on the allow-list (`customer_id` None). Otherwise `customer` with `customer_id` from the service's resolver `(request, tenant_id, token) -> customer_id | None`.
- Status: no/invalid/expired token, wrong audience or issuer -> 401 with `WWW-Authenticate: Bearer`. Valid token but tenant not a customer, or operator-tenant account not allow-listed -> 403. JWKS unreachable -> 503.
- Scoping: `caller.scope(customer_id)` for reads (operator: the optional filter, None = all; customer: own, another id -> 403). `caller.owner(customer_id)` for creates (operator: required, else 422; customer: own). `caller.require_operator()` for operator-only routes.

## Rules

- No bypass flag, no "dev without auth", no default that disables a check. Tests use `FakeIssuer`, which runs the real validation path.
- `testing.py` is never imported by service code.
