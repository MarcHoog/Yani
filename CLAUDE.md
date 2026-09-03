# yani

Personal project. Self-hosted MSP operating platform: graph SSOT + admin/staff portal + customer portal + ticketing + automations.
Monorepo. This folder is the git repo and the agentic workspace. Sub-agents get cwd pinned to one component folder.

## Scope override: personal project, not work

This repo is NOT a work project. The user's global `~/.claude/CLAUDE.md` contains work-only rules. Inside this repo:

- IGNORE global Azure DevOps rules. No AzDO, no `azdo-pull-request` skill, no AzDO PR conventions.
- IGNORE global "Bicep for infrastructure" default. Infra here is Docker Compose + Traefik config.
- IGNORE global "PowerShell, never Python/Node" default. Backend is Python (FastAPI), frontend is TypeScript. PowerShell only for repo helper scripts.
- IGNORE any Azure MCP / Azure best-practice tool nudges. Do not call Azure tools for this repo.
- KEEP: read before edit, implement exactly what was asked, no extra abstractions, error handling only at boundaries, state plan before changes, concise responses, no emojis, CRLF, Windows paths in scripts.
- Git host: GitHub, `https://github.com/MarcHoog/Yani.git`. Feature branches + pull requests. Never commit or push to `main` directly. Use the `github-pull-request` skill (PowerShell REST, no gh) for PRs. After every PR create or push, ask `Start AI review of PR #<n>?` and stop; only an explicit yes runs the `github-pr-review` skill, which self-fixes for at most 3 rounds and then asks again.

Preferred: run `.\claude.ps1` before starting Claude. It toggles `CLAUDE_CONFIG_DIR` to `.claude-home\` (run again = back to global), prints the active home. `.\claude.ps1 -Launch` sets it and starts claude. `-Status`, `-On`, `-Off` also available. With yani home active, global config, memory, plugins and hooks are not loaded at all. This section is the fallback when launched with global home.

## Hard constraints

- Zero Azure services or integrations in the product stack. No Entra, Azure APIM, App Service, Key Vault, Azure Monitor.
- Azure is allowed only as a TARGET of automations later (Prefect flows acting on customer tenants). Keep behind adapters.
- Everything runs as containers. Dev = `docker compose up`. Prod = same images, any container host.
- Internet and public registries (Docker Hub, npm, PyPI) are fine. No SaaS dependencies in the product.

## Decisions (2026-09-03)

| Concern | Decision |
|---|---|
| Layout | Monorepo, one folder per component |
| Backend | Python, FastAPI, uv workspace |
| Frontend | TypeScript, React, Vite, pnpm workspaces |
| SSOT store | Neo4j. Nodes = identity + relationships only (stable ID, name, type). No detail payloads. |
| Ticket store | Postgres. Structured fields as columns, text/comments/bodies as JSONB. No separate document DB. |
| Entity ownership | Every entity has one home DB. Other DBs store only its ID. Ticket lives in Postgres, Neo4j gets edge stub after commit. ULIDs everywhere. |
| UIs | Two: staff portal (SSOT admin + ticketing) and customer portal (read-only view + tickets + self-service) |
| Gateway | Traefik. Portals call APIs via gateway hostnames, same URLs dev and prod. |
| Identity | Zitadel container. Services validate JWT via JWKS only. Local users seeded for dev. |
| Login UI | Zitadel hosted login, branded to the theme (logo, colors, font). Portals redirect, never render credential forms. No custom login UI. |
| Automations | Mock executor first, Prefect server container later. Keep executor interface stable. |
| API contract | OpenAPI from FastAPI. TS clients generated, never hand-written. |
| Shared code | Python shared package (auth/JWT, settings, logging, db clients). React component library. |
| Attachments | MinIO (S3 API) when needed. |
| Mail | Mailpit in dev. |

## Current state

Building up slowly, design first. Architecture lives in `docs\architecture.md` (mermaid). Do not scaffold code folders until the user asks.

Scaffolded so far: `ui\` (`@yani/ui` component library, pnpm workspace root at repo root). See `ui\CLAUDE.md`.

Reference POC (read-only, do not modify): `C:\dev personal\personal-website\.playground\`
(ssot-api, ticket-api, ssot-portal, ticket-portal, user-portal). Port from there, do not copy blindly.

## Conventions

- Each component folder gets its own `CLAUDE.md` (stack, run, test, boundaries). Sub-agents read that first.
- Root helper script: `dev.ps1` (up, down, seed, logs, test). Agents use it, not raw docker commands.
- Python: ruff, strict Pydantic, type hints everywhere. TS: strict mode.
- No auth bypasses in code. Dev uses real Zitadel with seeded users.
