# Agent runs

Plan document. Nothing here is built yet. Describes the first slice of "send a card to an AI and
watch it work": where connections and their credentials live, the service that owns runs, and the
portal surface that starts one.

Companion to `docs\architecture.md`, which already reserves the `automation-api` box. This document
fills that box in.

## Scope of this slice

In:

- A `Connections` tab in the portal: create, edit, test connections to outside systems, with their
  credentials.
- A new `automation-api` component that owns connections, prompts and runs, with a worker that
  executes runs.
- A `Send to AI` button on a card that opens a dialog: pick a model, pick a prompt, dispatch.
- A mock executor, so the whole path is real end to end without anything being sandboxed yet.

Out, deliberately:

- Docker. No daemon connection, no containers, no images. The executor seam exists; only the mock
  implementation lands.
- Git checkout, pull requests, acting on real systems.
- Writing run results back onto the card.
- Approval gates, run profiles, SSE.

The point of the slice is that dispatch, storage, state and display are finished and boring before
anything is given a credential and a container.

## Component: automation-api

New folder `automation-api\`, FastAPI + asyncpg, same shape as `todo-api`. Same Postgres instance,
its own tables. Port 8020.

It does not read todo-api's tables. To render a prompt it calls todo-api over HTTP
(`TODO_API_URL=http://todo-api:8010`). Card stays owned by todo-api; a run stores `subject_id` and
nothing else about it.

```
src\automation_api\main.py              app, lifespan (pool, schema, seed prompts, start worker)
src\automation_api\config.py            Settings: DATABASE_URL, TODO_API_URL, EXECUTOR, SECRET_KEY, MODELS
src\automation_api\database.py          SCHEMA ddl, pool, ConnDep
src\automation_api\secrets.py           encrypt / decrypt / mask
src\automation_api\connections\         schemas, service, router, kinds\ (adapters)
src\automation_api\prompts\             schemas, service, router (render lives here)
src\automation_api\runs\                schemas, service, router
src\automation_api\executors\           base.py (protocol), mock.py
src\automation_api\worker.py            claim loop
```

### Tables

| table | columns |
|---|---|
| `connections` | `id` ULID, `kind`, `name`, `config` JSONB, `secret` bytea (encrypted, never read back), `created_at`, `updated_at` |
| `prompts` | `id`, `name`, `description`, `template`, `is_default`, timestamps |
| `runs` | `id`, `subject_type`, `subject_id`, `model`, `prompt_id`, `prompt_text`, `extra`, `connection_ids` JSONB, `state`, `result` JSONB, `error`, `created_at`, `started_at`, `finished_at` |
| `run_events` | `id`, `run_id`, `seq`, `at`, `kind`, `payload` JSONB |

Same conventions as todo-api: ULIDs, structured fields as columns, free text as JSONB, idempotent
`CREATE TABLE IF NOT EXISTS` in lifespan, SQL only in `service.py`.

## Connections

A connection is one outside system plus the credential to reach it. The tab is the single place a
credential is ever typed, and the only place one lives.

### Kinds in this slice

| kind | config | secret | test |
|---|---|---|---|
| `anthropic` | `{auth: "oauth" \| "api_key"}` | the token | `api_key`: call the Models API and return the account it belongs to. `oauth`: cannot be checked cheaply, returns `unverified` and is proven by the first run |
| `github` | `{api_url, owner}` | personal access token | `GET /user`, returns the login and the scopes header |

A kind is a string plus a small adapter in `connections\kinds\`. The adapter interface is two
functions and nothing else:

```python
class ConnectionKind(Protocol):
    config_model: type[BaseModel]
    async def test(self, config: BaseModel, secret: str) -> Identity: ...
```

`docker_host` becomes a third kind when Docker lands, and the tab is already the right place for it.
Not now.

### Secret handling

Rules, in order of how much they matter:

1. The secret is write-only over the API. Reads return `secret_set: bool` and `secret_hint` (last
   four characters), never the value.
2. `PATCH` semantics: field absent means unchanged, `""` means clear. There is no way to read one
   back to re-send it.
3. Never logged, never in a run event, never in an error message. The event writer scrubs known
   secret values before insert.
4. Encrypted at rest with Fernet, key from `YANI_SECRET_KEY`. Roughly fifteen lines and it keeps
   credentials out of database dumps, screenshots and the log pipeline. The lazy alternative is a
   plaintext column; the habit is worth more than the fifteen lines.

No auth on the API itself, per the standing rule. The credential is protected from leaking outward,
not from a local caller.

### Endpoints

```
GET    /api/v1/connections
POST   /api/v1/connections
GET    /api/v1/connections/{id}
PATCH  /api/v1/connections/{id}
DELETE /api/v1/connections/{id}
POST   /api/v1/connections/{id}/test    -> {ok, identity?, detail?}
```

`test` is what makes the tab worth having: a credential you have not exercised is a credential you
do not have.

## Prompts and models

A prompt is a named template. Templating stays dumb, `{{card.title}}`, `{{card.description}}`,
`{{card.todos}}`, `{{card.comments}}`, `{{extra}}`. Rendering happens server side, once, at dispatch,
and the rendered text is stored on the run. What ran is what you can read back; the run does not
re-render later against a card that has since changed.

```
GET  /api/v1/prompts
POST /api/v1/prompts
PATCH/DELETE /api/v1/prompts/{id}
POST /api/v1/prompts/{id}/render   {subject_type, subject_id, extra} -> {text}
```

The portal calls `render` for its preview, so the template language exists in exactly one place.

Seed with two or three: `Build a script`, `Investigate`, `Write a plan`.

Models come from `GET /api/v1/models`, a static list in config (`claude-opus-5`, `claude-sonnet-5`,
`claude-haiku-4-5`) with an env override. It is a picker, not a capability query.

## Runs

States: `queued` -> `running` -> `succeeded` | `failed` | `cancelled`. `needs_approval` joins later,
between queued and running, when a profile requires it.

```
POST /api/v1/runs          {subject_type, subject_id, model, prompt_id, extra} -> run
GET  /api/v1/runs?subject_id=...
GET  /api/v1/runs/{id}
GET  /api/v1/runs/{id}/events?after={seq}
POST /api/v1/runs/{id}/cancel
```

Events are polled with `after=seq` for now. The shape is already stream-ready, so SSE later is a
transport change and not a model change.

### Executor seam

The one abstraction this slice is allowed, because the whole point is to swap it later.

```python
class Executor(Protocol):
    async def run(self, run: Run, emit: Emit) -> Result: ...
```

`MockExecutor` sleeps, emits a handful of events including the prompt it was given, and returns
success. Chosen by `EXECUTOR=mock`. `DockerExecutor` is a second file that reads a `docker_host`
connection and starts a container; nothing else in the service changes when it arrives.

### Worker

One asyncio task started in lifespan. Claims with `SELECT ... FOR UPDATE SKIP LOCKED`, concurrency
from config, default 1. No Celery, no Prefect, no queue broker. The runs table is the queue.

Runs do not write to the card in this slice. The portal shows the run; nothing appears in the card
body.

## Portal

### Routing

The portal is currently one page. `Sidebar` already takes `href` and `onNavigate`, so navigation
needs a `useRoute()` of about twenty lines over `pushState` and `popstate`. No router dependency.

Routes: `/` board, `/connections`.

### Second API client

The portal now talks to two services. `/api/v1/...` stays todo-api. automation-api is proxied at
`/automation/api/v1/...` by vite in dev and nginx in the container, with its own generated
`src\api\automation.d.ts` and its own `pnpm gen:automation-api` script. Types stay generated; no
hand-written request or response shapes.

### Connections page

`portal\src\connections\`. A `Table` of connections, one row per connection, showing kind, name,
identity from the last test, and whether a secret is set. `Add connection` and row click open a
`SidePanel` form: kind `Select`, name, the config fields for that kind, secret `Input`
type=password with placeholder `unchanged`. A `Test` button runs the test and reports through
`Notice`.

### Send to AI

A `Send to AI` button in the `CardPanel` actions. It opens a dialog, not a second side panel,
because a panel over a panel reads badly.

Dialog contents:

- Model `Select`, from `GET /models`.
- Prompt `Select`, from `GET /prompts`.
- Extra instructions `Textarea`.
- A read-only preview of the rendered prompt, refreshed from `POST /prompts/{id}/render` when either
  select or the textarea settles.
- Dispatch, which posts the run and closes.

Below the card's comments, a `Runs` section lists that card's runs with a state `Badge` and a
timestamp. Clicking one shows its events. That is the entire feedback surface in this slice.

The per-comment trigger, which is where this idea started, is the same dialog seeded with a comment's
text. It lands once the card-level path works.

### ui additions

One new component in `@yani\ui`: `Dialog`. Modal, `--scrim` behind, `--shadow-lg` on the surface,
escape and backdrop close, focus trap. Everything else is already there: `Table`, `Field`, `Input`,
`Select`, `Textarea`, `Badge`, `Notice`, `SidePanel`, `Button`.

## Compose

```
automation-api:  port 8020, depends on postgres healthy
                 DATABASE_URL, TODO_API_URL, EXECUTOR=mock, YANI_SECRET_KEY
portal nginx:    proxy /automation/ -> automation-api:8020
vite dev:        same proxy to localhost:8020
```

## What the container image will need, later

Recorded now because it constrains the API shape, not because it is in this slice. The run image is
ours to build: the Agent SDK, git, a toolchain, and yani's own MCP server pointed back at the stack
so the agent can read the card and the graph it is working on. That means a run needs to carry its
own identity to the MCP surface it is given, and the surface has to be narrower than the portal's.
Neither exists yet; `runs` already has the `id` that will become that identity.

## PR sequence

Stacked, one component each.

1. `automation-api` skeleton: folder, `CLAUDE.md`, schema, connections CRUD, kind adapters, test
   endpoint, secrets, compose entry.
2. `automation-api`: prompts, render, models.
3. `automation-api`: runs, events, mock executor, worker.
4. `ui`: `Dialog`.
5. `portal`: routing, second API client, Connections page.
6. `portal`: Send to AI dialog and the runs list on the card.

## Open

- Does `automation-api` own connections long term, or do they become their own thing once ssot-api
  and the MCP server also need credentials? Owning them here is right while runs are the only
  consumer.
- One `anthropic` connection assumed to be the default. Explicit per-run selection, or a `default`
  flag per kind?
- Whether `subject_type` is worth having before anything but `card` exists. Cheap now, awkward to add
  later.
- Where run output eventually lands on the card: a comment, a dedicated section, or an attachment.
