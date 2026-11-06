# yani

Managed layer on top of Microsoft 365 (later Google Workspace) for small and medium businesses. Opinionated, heavily automated, one standard way of doing every common thing (users, shared mailboxes, groups, devices, licenses). Operators run it; customers get a read-only overview of their tenant and cost, and ask for changes through published forms. Every form runs through a standard: plan, approve, apply, log. Drift from the standard is detected and shown.

Read `docs\vision.md` (what and why), `docs\architecture.md` (how), `docs\roadmap.md` (what exists, what's next) before designing anything.

Monorepo. This folder is the git repo and the agentic workspace. Sub-agents get cwd pinned to one component folder.

## Scope override: own project, not employer work

This repo is Marc's own project. The user's global `~/.claude/CLAUDE.md` contains employer work rules. Inside this repo:

- IGNORE global Azure DevOps rules. No AzDO, no `azdo-pull-request` skill, no AzDO PR conventions.
- IGNORE global "Bicep for infrastructure" default. Infra here is Docker Compose.
- IGNORE global "PowerShell, never Python/Node" default. Backend is Python (FastAPI), frontend is TypeScript. PowerShell only for repo helper scripts.
- IGNORE any Azure MCP / Azure best-practice tool nudges. Do not call Azure tools for this repo.
- KEEP: read before edit, implement exactly what was asked, no extra abstractions, error handling only at boundaries, state plan before changes, concise responses, no emojis, CRLF, Windows paths in scripts.
- Git host: GitHub, `https://github.com/MarcHoog/Yani.git`. Feature branches + pull requests. Never commit or push to `main` directly. Use the `github-pull-request` skill (Python REST, no gh, cross-platform) for PRs and the `github-pr-comments` skill to read PR feedback. After every PR create or push, ask the "Next step?" question (review with 2 agents / review with 1 agent / resolve comments / make more changes / PR merged - clear worktree / other) and stop; only an explicit review answer runs the `github-pr-review` skill, which self-fixes for at most 3 rounds and then asks again.

Preferred: run `.\claude.ps1` before starting Claude. It toggles `CLAUDE_CONFIG_DIR` to `.claude-home\` (run again = back to global), prints the active home. `.\claude.ps1 -Launch` sets it and starts claude. `-Status`, `-On`, `-Off` also available. With yani home active, global config, memory, plugins and hooks are not loaded at all. This section is the fallback when launched with global home.

## Hard constraints

- No Azure platform services in the product stack: no App Service, Azure APIM, Key Vault, Azure Monitor, Azure SQL. Yani does not run on Azure.
- Microsoft 365, Entra, Exchange Online and Intune are what yani manages: targets, reached only through adapters in `automation-api`. That is integration, not hosting.
- Identity is yani's own: a self-hosted Zitadel container in the compose stack. Users sign in to Zitadel, never directly to Microsoft or Google; those become identity providers inside Zitadel later, with no code change in the services.
- Everything runs as containers. Dev = `docker compose up`. Prod = same images, any container host.
- Internet and public registries (Docker Hub, GHCR, npm, PyPI) are fine. No SaaS dependencies in the product beyond the tenants it manages (and, later, Microsoft/Google as upstream sign-in behind Zitadel).
- Authentication is required. Every API validates Zitadel JWTs via the issuer's JWKS. No auth bypass flags, no "dev without auth" mode.
- Tenant isolation: a customer token only ever reaches its own `customer_id`, enforced server-side in every service.

## Decisions (2026-09-03, repivoted 2026-09-08, back to the managed SMB service 2026-11-06, identity to Zitadel 2026-11-06)

| Concern | Decision |
|---|---|
| Product | Managed M365 layer for SMBs. Operator runs changes; customer is read-only plus forms. See `docs\vision.md`. |
| Layout | Monorepo, one folder per component |
| Backend | Python, FastAPI, uv workspace |
| Frontend | TypeScript, React, Vite, pnpm workspaces |
| Inventory | Neo4j via `ssot-api`. Synced tenant model: customers, tenants, users, groups, mailboxes, devices, license SKUs, relationships. Nodes = identity + relationships + minimal query props, `customer_id`, external ID. No payloads. |
| Requests | Postgres via `todo-api`. A request = customer + standard version + answers + state. Operator works them as cards on a board. Text as JSONB. |
| Standards and forms | One versioned definition: form JSON schema + plan template + checks. Data, not code; a fixed set of step types in code. Published per customer. |
| Execution | `automation-api`: connections (encrypted secrets), plans, runs, run events, worker on the runs table, executor seam (mock first), tenant sync, drift checks. |
| Tenant access | Adapters per capability (users, groups, mailboxes, devices, licenses). M365 first, Google later behind the same interfaces. |
| Entity ownership | Every entity has one home DB. Other DBs store only its ID. ULIDs everywhere. |
| Identity | Self-hosted Zitadel (compose, own Postgres). Local users (username + password, MFA available) now; Microsoft/Google sign-in later as identity providers inside Zitadel. One Zitadel organization per customer plus one operator organization. Project `yani` (owned by the operator org) with roles `operator` and `customer`; customer orgs get a project grant with `customer` only. Token = JWT access token, audience = project ID; role from Zitadel's project role claim (`operator` only when granted by the operator org), `customer_id` = the customer's Zitadel organization ID. See `docs\architecture.md` section 2. |
| UI | Operator console (`portal\`) and a customer portal, same `@yani/ui` style system. |
| AI interface | `mcp-server`, operator only: thin MCP adapter over the REST APIs. No model calls inside yani itself. |
| API contract | OpenAPI from FastAPI. TS clients generated, never hand-written. |
| Shared code | Python shared package (settings, logging, db clients). React component library. |
| Attachments | MinIO (S3 API) when needed. |
| Mail | Mailpit in dev. |

## Current state

Docs are the source of truth for direction; code still reflects the short-lived personal todo board and is being repurposed slice by slice (`docs\roadmap.md`). Do not scaffold new component folders until the user asks.

Scaffolded so far:
- `ui\` (`@yani/ui` component library, pnpm workspace root at repo root). See `ui\CLAUDE.md`.
- `shared\` (`yani-shared` Python package: auth via JWKS, caller role and customer scoping). See `shared\CLAUDE.md`.
- `ssot-api\` (FastAPI + Neo4j, the inventory; uv workspace root at repo root). See `ssot-api\CLAUDE.md`.
- `todo-api\` (FastAPI + Postgres, board columns, cards, inbox; becomes requests). See `todo-api\CLAUDE.md`.
- `portal\` (`@yani/portal`, becomes the operator console; board page today). See `portal\CLAUDE.md`.

Zitadel runs in compose (`python dev.py up`, then `python dev.py seed` for orgs, project, portal app and test users). ssot-api and todo-api require a valid token on every `/api/v1` route and scope everything by `customer_id` (slice 1, backend part). The portal has no sign-in yet, so it cannot talk to the APIs until slice 1 part 2.

UI style: `docs\style.md` (principles, tokens, scale, for humans). Agent rules distilled in `ui\CLAUDE.md` under Style. Anything visual follows both.

Reference POC (read-only, do not modify): `C:\dev personal\personal-website\.playground\`
(ssot-api, ticket-api, ssot-portal, ticket-portal, user-portal). Port from there, do not copy blindly.

## Conventions

- Each component folder gets its own `CLAUDE.md` (stack, run, test, boundaries). Sub-agents read that first.
- Root helper script: `dev.py` (up, down, seed, logs, test), run as `python dev.py <command>`. Agents use it, not raw docker commands. `seed` runs `seed_zitadel.py`.
- Python: ruff, strict Pydantic, type hints everywhere. TS: strict mode.
