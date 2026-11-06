# portal

`@yani/portal`. Becomes the operator console (requests board, inventory, runs, standards; see `docs\roadmap.md`). Today: kanban board with an inbox from the earlier personal-board phase. Composes `@yani/ui` components; talks to todo-api.

## Stack

React 19, Vite 8, TypeScript strict, pnpm workspace member. API types generated from the todo-api OpenAPI schema (openapi-typescript), calls via openapi-fetch. No router yet (single page), no global state.

## Run

From repo root: `python dev.py up`, then `python dev.py seed`; portal on http://localhost:8080 (nginx serves the build, proxies `/api` to todo-api and renders `/auth-config.json` from env). Sign in with the seeded operator.
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
nginx.conf.template     container nginx config, rendered with envsubst at start
index.html              theme head script (copied from ui), root div
src\main.tsx            imports @yani/ui theme.css and app.css, renders App
src\App.tsx             Sidebar + main region
src\app.css             app shell layout, page-level classes
src\api\schema.d.ts     GENERATED from todo-api openapi.json. Never edit; pnpm gen:api
src\api\client.ts       openapi-fetch client, relative base url, bearer token middleware (401 -> sign in)
src\auth\auth.ts        oidc-client-ts UserManager from /auth-config.json: sign in, callback, sign out, token
src\auth\AuthGate.tsx   renders the app only for a signed-in user, handles /auth/callback
src\board\useBoard.ts   board state: load, add card, move card (optimistic + reload), update card
src\board\BoardPage.tsx page: PageHeader, composer, Board and CardPanel wiring
src\board\CardPanel.tsx card detail in a SidePanel: title, description, todo, comments
src\board\cardBody.ts   the `{description, todos, comments}` shape stored in the card `body` JSONB
src\board\cardMeta.tsx  todo progress and comment count shown on the board card
src\inbox\useInbox.ts  inbox state: load, add, update, remove, promote to a column, attach to a card
src\inbox\inboxItem.ts drag type and the `{description}` shape stored in the inbox item `body`
src\inbox\InboxItemPanel.tsx inbox item detail in a SidePanel: title, description
```

## Rules

- All API calls same-origin `/api/v1/...`. Vite proxies in dev, nginx proxies in the container. No CORS, no API base url config.
- API types come from `pnpm gen:api` against a running todo-api. Never hand-write request/response types. Changed the API? Regenerate and commit.
- Generic visuals belong in `ui\` (`@yani/ui`); this package only composes them and wires data. Style rules: `ui\CLAUDE.md`, `docs\style.md`.
- Domain icons (lucide) are chosen here and passed into ui components as props.
- Card detail (description, todo, comments) lives in the card `body` JSONB, parsed in `cardBody.ts`. `writeCardDetail` keeps unknown keys because PATCH replaces the whole `body`.
- The inbox sits left of the board and is not a column. Dragging an item onto a column calls `promote` (new card), onto a card calls `attach` (todo + comment). Both are todo-api endpoints; the portal only reloads afterwards.
- Sign-in: OIDC code + PKCE against Zitadel (`docs\architecture.md` section 2). Issuer, client ID and project ID come from `/auth-config.json` at runtime (nginx template in the container, a vite plugin reading the root `.env` in dev), so one image fits every environment. Tokens live in sessionStorage. Every API call goes through `api` in `client.ts`, which adds the token. No bypass flags, no "dev without auth" mode.
