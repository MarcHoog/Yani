# yani

Personal project. Self-hosted automation / todo kanban worker for one user (Marc): graph SSOT (work knowledge as a queryable graph instead of markdown) + todo kanban board + automations + MCP server so Claude Desktop/Code can query and work the board directly.
Monorepo. This folder is the git repo and the agentic workspace. Sub-agents get cwd pinned to one component folder.

## Scope override: personal project, not work

This repo is NOT a work project. The user's global `~/.claude/CLAUDE.md` contains work-only rules. Inside this repo:

- IGNORE global Azure DevOps rules. No AzDO, no `azdo-pull-request` skill, no AzDO PR conventions.
- IGNORE global "Bicep for infrastructure" default. Infra here is Docker Compose.
- IGNORE global "PowerShell, never Python/Node" default. Backend is Python (FastAPI), frontend is TypeScript. PowerShell only for repo helper scripts.
- IGNORE any Azure MCP / Azure best-practice tool nudges. Do not call Azure tools for this repo.
- KEEP: read before edit, implement exactly what was asked, no extra abstractions, error handling only at boundaries, state plan before changes, concise responses, no emojis, CRLF, Windows paths in scripts.
- Git host: GitHub, `https://github.com/MarcHoog/Yani.git`. Feature branches + pull requests. Never commit or push to `main` directly. Use the `github-pull-request` skill (Python REST, no gh, cross-platform) for PRs and the `github-pr-comments` skill to read PR feedback. After every PR create or push, ask the "Next step?" question (review with 2 agents / review with 1 agent / resolve comments / make more changes / PR merged - clear worktree / other) and stop; only an explicit review answer runs the `github-pr-review` skill, which self-fixes for at most 3 rounds and then asks again.

Preferred: run `.\claude.ps1` before starting Claude. It toggles `CLAUDE_CONFIG_DIR` to `.claude-home\` (run again = back to global), prints the active home. `.\claude.ps1 -Launch` sets it and starts claude. `-Status`, `-On`, `-Off` also available. With yani home active, global config, memory, plugins and hooks are not loaded at all. This section is the fallback when launched with global home.

## Hard constraints

- Zero Azure services or integrations in the product stack. No Entra, Azure APIM, App Service, Key Vault, Azure Monitor.
- Azure is allowed only as a TARGET of automations later (Prefect flows acting on work tenants/systems). Keep behind adapters.
- Everything runs as containers. Dev = `docker compose up`. Prod = same images, any container host.
- Internet and public registries (Docker Hub, npm, PyPI) are fine. No SaaS dependencies in the product.

## Decisions (2026-09-03, repivoted 2026-09-08)

| Concern | Decision |
|---|---|
| Layout | Monorepo, one folder per component |
| Backend | Python, FastAPI, uv workspace |
| Frontend | TypeScript, React, Vite, pnpm workspaces |
| SSOT store | Neo4j. Nodes = identity + relationships only (stable ID, name, type). No detail payloads. Catalog to be repurposed from MSP entities to Marc's work landscape. |
| Todo store | Postgres. Cards on a kanban board. Structured fields as columns, text/comments/bodies as JSONB. Columns are data rows, not an enum. No separate document DB. |
| Entity ownership | Every entity has one home DB. Other DBs store only its ID. Card lives in Postgres, Neo4j gets edge stub after commit. ULIDs everywhere. |
| UI | One portal: kanban board + graph explorer, same style system. |
| AI interface | `mcp-server` component: thin MCP adapter (streamable HTTP, localhost) over the REST APIs. Claude Desktop/Code connect via subscription — no API key on this path. No model calls inside yani itself for now. |
| Gateway | None for now. Plain localhost ports. Reverse proxy returns only if the stack ever serves more than one machine. |
| Identity | None. Single user, local network only. No auth code, no bypass flags to remove later. |
| Automations | Mock executor first, Prefect server container later. Keep executor interface stable. Automations may create/move cards. |
| API contract | OpenAPI from FastAPI. TS clients generated, never hand-written. |
| Shared code | Python shared package (settings, logging, db clients). React component library. |
| Attachments | MinIO (S3 API) when needed. |
| Mail | Mailpit in dev. |

## Current state

Building up slowly, design first. Architecture lives in `docs\architecture.md` (mermaid). Do not scaffold code folders until the user asks.

Scaffolded so far:
- `ui\` (`@yani/ui` component library, pnpm workspace root at repo root). See `ui\CLAUDE.md`.
- `ssot-api\` (FastAPI + Neo4j, uv workspace root at repo root, `compose.yaml` with neo4j + ssot-api, `dev.ps1`). See `ssot-api\CLAUDE.md`.
- `todo-api\` (FastAPI + Postgres, kanban columns and cards, port 8010, postgres + todo-api in `compose.yaml`). See `todo-api\CLAUDE.md`.
- `portal\` (`@yani/portal`, the one UI: kanban board page on todo-api, port 8080 in compose / 5174 dev). See `portal\CLAUDE.md`.

UI style: `docs\style.md` (principles, tokens, scale, for humans). Agent rules distilled in `ui\CLAUDE.md` under Style. Anything visual follows both.

Reference POC (read-only, do not modify): `C:\dev personal\personal-website\.playground\`
(ssot-api, ticket-api, ssot-portal, ticket-portal, user-portal). Port from there, do not copy blindly.

## Conventions

- Each component folder gets its own `CLAUDE.md` (stack, run, test, boundaries). Sub-agents read that first.
- Root helper script: `dev.ps1` (up, down, seed, logs, test). Agents use it, not raw docker commands.
- Python: ruff, strict Pydantic, type hints everywhere. TS: strict mode.
- No auth in the product at all (single user, local). Do not add auth scaffolding, middleware, or bypass flags.
