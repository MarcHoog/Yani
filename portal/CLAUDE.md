# portal

`@yani/portal`. The one yani UI: kanban board now, graph explorer later. Composes `@yani/ui` components; talks to todo-api.

## Stack

React 19, Vite 8, TypeScript strict, pnpm workspace member. API types generated from the todo-api OpenAPI schema (openapi-typescript), calls via openapi-fetch. No router yet (single page), no global state.

## Run

From repo root: `.\dev.ps1 up` builds and serves everything; portal on http://localhost:8080 (nginx serves the build and proxies `/api` to todo-api).
Dev: `pnpm install` at repo root, start todo-api (see `todo-api\CLAUDE.md`), then from `portal\`: `pnpm dev` on http://localhost:5174 (vite proxies `/api` to localhost:8010).

| command (from `portal\`) | does |
|---|---|
| `pnpm dev` | vite dev server, port 5174 |
| `pnpm build` | typecheck + production build |
| `pnpm typecheck` | tsc |
| `pnpm lint` | oxlint |
| `pnpm gen:api` | regenerate `src\api\schema.d.ts` from a running todo-api |

## Layout

```
index.html              theme head script (copied from ui), root div
src\main.tsx            imports @yani/ui theme.css and app.css, renders App
src\App.tsx             Sidebar + main region
src\app.css             app shell layout, page-level classes
src\api\schema.d.ts     GENERATED from todo-api openapi.json. Never edit; pnpm gen:api
src\api\client.ts       openapi-fetch client, relative base url
src\board\useBoard.ts   board state: load, add card, move card (optimistic + reload), update card
src\board\BoardPage.tsx page: PageHeader, composer, Board and CardPanel wiring
src\board\CardPanel.tsx card detail in a SidePanel: title, description, todo, comments
src\board\cardBody.ts   the `{description, todos, comments}` shape stored in the card `body` JSONB
```

## Rules

- All API calls same-origin `/api/v1/...`. Vite proxies in dev, nginx proxies in the container. No CORS, no API base url config.
- API types come from `pnpm gen:api` against a running todo-api. Never hand-write request/response types. Changed the API? Regenerate and commit.
- Generic visuals belong in `ui\` (`@yani/ui`); this package only composes them and wires data. Style rules: `ui\CLAUDE.md`, `docs\style.md`.
- Domain icons (lucide) are chosen here and passed into ui components as props.
- Card detail (description, todo, comments) lives in the card `body` JSONB, parsed in `cardBody.ts`. `writeCardDetail` keeps unknown keys because PATCH replaces the whole `body`.
- No auth, by design. Single-user local app.
