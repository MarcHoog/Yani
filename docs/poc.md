# yani POC: core platform on mock tenants

Working state for the `/poc-loop` skill. The loop reads this file at the start of every iteration
and updates it at the end. Humans edit it too: reorder tasks, add notes, unblock things.

## Goal

The whole platform works end to end with real identity, real databases and real services. The
only fake part is the customer tenant: a `MockAdapter` behind the same adapter interfaces the M365
adapter will implement later (`docs\architecture.md` section 3). Swapping mock for M365 must be an
adapter change, nothing else.

In scope: roadmap slices 1 part 2, 2, 3, 5, 6, with slice 4 (sync) running against the mock
adapter. Out of scope: anything that talks to Microsoft or Google, cost beyond a fixed price table,
drift (stretch only), `mcp-server`.

## Demo script (definition of done)

From a clean checkout: `python dev.py down -v`, `python dev.py up`, `python dev.py seed`. Then:

1. Operator signs in to the operator console through Zitadel.
2. Inventory page shows customer "Bakkerij Peeters": users, groups, shared mailboxes, devices,
   license SKUs and their relations. The data got there through a sync run reading the mock
   tenant via `MockAdapter` and writing into `ssot-api`, not through a direct seed into Neo4j.
3. Runs page shows that sync run with its events.
4. A customer user of Bakkerij Peeters signs in to the customer portal. They see only their own
   tenant, and the published form "New employee".
5. They submit "Jan Peeters, Sales, starts 1 December, needs a laptop". The request shows as
   `submitted`, then `planned`.
6. The operator sees the request as a card on the board, opens it, sees the answers, the plan
   steps and the monthly cost delta, and approves.
7. A run executes the plan through `MockAdapter` (the mock tenant now contains Jan), the inventory
   is updated, run events are visible, the request ends `done`.
8. The customer sees the request `done` and Jan in their overview.
9. A customer user of a second customer, "Studio Janssens", sees none of this (UI and API).

`python dev.py test` is green, and `python dev.py e2e` runs steps 1 to 9 in a browser.

## Decisions for the POC

Made up front so the loop does not stall on them. Each one is recorded in
`docs\architecture.md` when the task that relies on it lands.

- Mock tenant state lives in `automation-api` Postgres (one JSONB document per mock tenant),
  initialised from fixture files in `automation-api\fixtures\mock_tenants\`. Writes through
  `MockAdapter` persist, so a later sync sees them.
- Connection kind `mock` next to `m365`. Same secret handling (Fernet), the test endpoint returns
  the fixture's tenant name.
- Service-to-service calls (`automation-api` to `ssot-api` and `todo-api`) use a Zitadel machine
  user in the operator organization with the `operator` role. `dev.py seed` creates it and writes
  its credentials to `.env`. No shared secrets between services, no auth bypass.
- Standards are JSON files in the repo (`automation-api\standards\`), loaded into Postgres at
  startup. Authoring in the console is later.
- Request owns state (`todo-api`); plan and run own execution (`automation-api`).
  `automation-api` reports run outcome back to `todo-api`.
- Customer portal is its own app, `customer-portal\` (`@yani/customer-portal`), on `@yani/ui`.
- License prices: a fixed list-price table in `automation-api` Postgres, seeded.

## Milestones and tasks

Rules: work top to bottom. One task per iteration. A task is done only when its verification
passed. At the end of each milestone the loop opens or updates the PR and stops for review.

### M1 Identity end to end

- [ ] 1.1 Portal sign-in: OIDC code + PKCE against Zitadel, route guard, sign-out, token on every
      API call, 401 sends the user back to sign-in. Seed registers the redirect URIs.
- [ ] 1.2 Seed: second customer org "Studio Janssens" with project grant and a customer user.
      Rename the first test customer org to "Bakkerij Peeters". Idempotent.
- [ ] 1.3 Portal shows the signed-in user and role; board works against the authenticated
      `todo-api`. Manual check against the running stack recorded in the log.

### M2 Inventory model

- [ ] 2.1 `ssot-api` catalog to the tenant model: Customer, Tenant, User, Group, Mailbox, Device,
      LicenseSku and the edges from `docs\architecture.md` section 4. `external_id`,
      `customer_id`, ULIDs. Old MSP-era labels removed. Tests including isolation.
- [ ] 2.2 `ssot-api` reads the overview needs: list nodes by label for a customer, node with
      neighbours, upsert by `external_id` (for sync). Scoped, tested.
- [ ] 2.3 Portal routing (board, inventory, runs) and inventory page: customer switcher, a table
      per type, side panel with a user's groups, mailboxes, device and license.

### M3 automation-api and mock tenant

- [ ] 3.1 Scaffold `automation-api` (FastAPI, Postgres schema, `yani-shared` auth, compose
      service, `dev.py` PACKAGES, `CLAUDE.md`). Health and an authenticated whoami route.
- [ ] 3.2 Adapter interfaces per capability (users, groups, mailboxes, devices, licenses) and
      `MockAdapter` on the Postgres-backed mock tenant. Fixtures for both test customers.
- [ ] 3.3 Connections: kinds `mock` and `m365`, Fernet secrets, write-only secret rules from
      `docs\architecture.md` section 3, test endpoint. `m365` test may return "not implemented".
- [ ] 3.4 Runs table as queue, worker (`FOR UPDATE SKIP LOCKED`), append-only run events polled
      with `after=seq`, `Executor` seam with `MockExecutor`. Secret scrubbing in the event writer.
- [ ] 3.5 Machine user for service calls (seed), and a client in `automation-api` that gets and
      caches its token.
- [ ] 3.6 Sync run kind: read every capability through the adapter, reconcile into `ssot-api` by
      `external_id` (create, update, remove). Seed creates the `mock` connections and triggers
      the first sync.
- [ ] 3.7 Portal runs page: list runs, run detail with events.

### M4 Standards and requests

- [ ] 4.1 Standards: versioned definition (form JSON schema, plan template, checks), fixed step
      types in code, loaded from `automation-api\standards\`, published per customer. First:
      `new-employee` v1. Validate-answers endpoint.
- [ ] 4.2 `todo-api` cards become requests: `customer_id`, standard id and version, answers
      JSONB, state machine from `docs\architecture.md` section 6. Board columns are states.
      Customer can create and read own requests only.
- [ ] 4.3 Plan building: template plus current inventory to ordered steps with cost delta (price
      table). Request moves to `planned`.
- [ ] 4.4 Approve and run: operator approves in `todo-api`, run starts in `automation-api`,
      executor walks steps through `MockAdapter`, inventory updated (targeted sync), outcome
      reported back, request `done` or `failed`. Reject and cancel paths.
- [ ] 4.5 Console request card: answers, plan steps, cost delta, approve and reject, live run
      events.

### M5 Customer portal

- [ ] 5.1 Scaffold `customer-portal` (pnpm workspace, `@yani/ui`, sign-in, customer role only,
      compose service).
- [ ] 5.2 Overview: people, groups, shared mailboxes, devices, licenses, in plain language.
- [ ] 5.3 Forms rendered from the standard's JSON schema, submit, "My requests" with state.

### M6 Demo

- [ ] 6.1 `python dev.py e2e`: Playwright run of the demo script against the compose stack,
      real Zitadel sign-in for operator, customer A and customer B.
- [ ] 6.2 Docs: roadmap and architecture updated to what was built, demo walkthrough below.

### Stretch (only after M6)

- [ ] S.1 Cost: cost per user and per department on the customer overview.
- [ ] S.2 Drift: one check from `new-employee` (or a licensed shared mailbox) evaluated after
      sync, finding shown to operator and customer.
- [ ] S.3 Second standard: shared mailbox.

## Current

Status: stopped
Branch: agent/wizardly-fermat-0kyucu (named by the cloud session)
PR: https://github.com/MarcHoog/Yani/pull/28
Task: 1.1 (code in, not verified against Zitadel)
Plan: portal loads issuer, client ID and project ID from /auth-config.json (nginx template,
vite plugin in dev); oidc-client-ts code + PKCE; AuthGate around the app; bearer middleware on
the API client, 401 to sign-in; sign-out in the sidebar; seed keeps redirect URIs current for
8080 and 5174 and writes PORTAL_CLIENT_ID to .env.

## Blocked

- 1.1, 1.2, 1.3: the cloud environment cannot pull `ghcr.io/zitadel/zitadel` (network policy
  denies `pkg-containers.githubusercontent.com`, GHCR's blob host; Docker Hub works). Without a
  running Zitadel there is no real sign-in to verify. Unblock: allow that host in the
  environment's network settings, or run the loop locally. 1.1 code is committed; what remains is
  the stack check listed in the Log.

## Later

Ideas noticed during the loop that are out of scope. Not worked by the loop.

## Log

Newest last. One entry per iteration: date, task, commit, what was verified, what was not.

- 2026-11-06 1.1 (not ticked) - verified: portal typecheck, build and oxlint; ruff on
  seed_zitadel.py and dev.py; `python dev.py test` (24 + 10 + 18 passed); nginx template served
  from nginx:1.29-alpine renders /auth-config.json and keeps SPA deep links (200); Chromium
  against that container is redirected to `<issuer>/oauth/v2/authorize` with response_type code,
  S256 PKCE, the right client ID, callback and scopes (discovery stubbed in the browser only).
  Not verified: Zitadel itself (image pull denied), so no real sign-in, token exchange, API call
  with the token, 401 path, sign-out, or the seed's PUT oidc_config update path. `docker compose
  build portal` failed in this sandbox because the build container does not trust the session's
  proxy CA (environment, not the Dockerfile). Stopped: 1.1 to 1.3 all need Zitadel.
