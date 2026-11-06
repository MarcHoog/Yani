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
src\yani_shared\auth.py      AuthSettings (AUTH_* env), JwksCache, Auth dependency, Caller, caller_from_claims, Unauthorized, Forbidden
src\yani_shared\testing.py   FakeIssuer: test RSA key, discovery + JWKS over real localhost HTTP, Zitadel-shaped token minter. Tests only
tests\                       Auth against a throwaway FastAPI app
```

## Auth

- Issuer is yani's Zitadel. `AUTH_ISSUER` (e.g. `http://zitadel.localhost:8081`), `AUTH_AUDIENCE` (the Zitadel `yani` project ID) and `AUTH_OPERATOR_ORG` (the operator organization ID). All required; a service without them does not start. `python dev.py seed` writes the last two to `.env`.
- Signing keys: `<issuer>/.well-known/openid-configuration` -> `jwks_uri`, refetched on an unknown `kid` at most once a minute (failed attempts count too). Unusable keys are skipped; an unreachable or malformed discovery/JWKS response is 503.
- Token: RS256 only, signature, exact `iss`, `aud` contains the project ID, `exp`, `sub` present.
- Caller from `urn:zitadel:iam:org:project:<AUTH_AUDIENCE>:roles` (`{role: {org id: domain}}`): `operator` -> operator, `customer_id` None, only when granted by exactly `AUTH_OPERATOR_ORG`. `customer` -> customer, `customer_id` = the single org id, never the operator org. No yani role, both roles, an operator role from another org, or a customer role from several orgs -> 403. Roles of other projects are ignored.
- Status: no/invalid/expired token, wrong issuer or audience -> 401 with `WWW-Authenticate: Bearer`. Valid token without a usable yani role -> 403.
- Scoping: `caller.scope(customer_id)` for reads (operator: the optional filter, None = all; customer: own, another id -> 403). `caller.owner(customer_id)` for creates (operator: required, else 422). `caller.require_operator()` for operator-only routes.

## Rules

- No bypass flag, no "dev without auth", no default that disables a check. Tests use `FakeIssuer`, which runs the real validation path; no Zitadel in tests.
- No Zitadel API calls here: the services only validate tokens. Zitadel setup lives in `seed_zitadel.py` (repo root, `python dev.py seed`).
- `testing.py` is never imported by service code.
