# yani roadmap

Where the code is today against `docs\vision.md` and `docs\architecture.md`, and the order to build
the rest. Updated as slices land.

## Today (2026-11-06)

The repo was briefly repivoted to a personal todo board and is now back to the managed SMB
service. What exists was built for the personal board; most of it is reusable.

| component | exists | keeps | changes |
|---|---|---|---|
| `ui` (`@yani/ui`) | ~20 components, stories, screenshot tests | all of it; Table, SidePanel, Field, Badge, Notice, Meter, StatTile, CustomerSwitcher fit the product directly | add `Dialog`, form renderer pieces |
| `ssot-api` | node and relation CRUD on Neo4j, catalog validation, tests | the service and the catalog mechanism | catalog to the tenant model (User, Group, Mailbox, Device, LicenseSku), `customer_id` and external ID on nodes, auth |
| `todo-api` | board columns, cards, inbox with promote and attach, tests | board as the operator's request view | cards become requests (customer, standard, answers, state); inbox likely goes; auth and customer scoping |
| `portal` | board page, card panel, inbox | becomes the operator console | routing, inventory and runs pages, sign-in |
| compose, `dev.py` | neo4j, postgres, both APIs, portal; up, down, logs, test | as is | new services, seed with a fake customer |

Not built: portal sign-in, `automation-api`, adapters, standards and forms, sync, drift, cost,
customer portal, `mcp-server`.

## Slices

Each slice is one or more small PRs and ends with something that works end to end.

1. **Auth and tenancy.** Self-hosted Zitadel in compose with a seed (operator org, test customer
   org, users, project and app). Part 1 (backends): shared auth package, JWT validation via JWKS
   in both APIs, operator vs customer role from the Zitadel role claim, `customer_id` on every row
   and node, server-side scoping, tests that a customer token cannot see another customer.
   Part 2: OIDC sign-in in the portal.
2. **Inventory model.** New catalog in `ssot-api`, external IDs, seed script with one fake
   customer tenant. Operator console inventory page.
3. **automation-api skeleton.** Connections (`m365` kind) with encrypted secrets and test, runs
   table, worker, mock executor.
4. **Sync.** Real read-only sync from one test tenant into the inventory. First time yani touches
   Microsoft 365, and only reading.
5. **Standards and requests.** Standard definitions with form schema and plan template, requests in
   `todo-api`, plan building, operator approval, mock execution. First standard: new employee.
6. **Customer portal.** Read-only overview, published forms rendered from schema, request status.
7. **Real execution.** M365 adapter writes for the first standard, idempotent steps, retries.
8. **Cost.** SKU prices, cost per user and department, cost delta on plans.
9. **Drift.** Checks per standard after sync, findings for operator and customer.
10. **More standards.** Employee leaves, shared mailbox, device, access change.
11. **mcp-server** for the operator.
12. **Google Workspace adapter.**

Slices 1 to 3 can start now. Slice 4 needs a test tenant and the tenant-access decision
(`docs\architecture.md` section 10).
