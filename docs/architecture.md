# yani architecture

Living document. Grows as decisions are made. Nothing here is implemented yet.

## 1. System overview

Who talks to what. Every box is a container in one `docker compose` stack.
Login is Zitadel's hosted page, branded to the portal theme. Portals only redirect to it and never render credential forms.

```mermaid
flowchart LR
    staff([MSP staff])
    customer([Customer employee])

    subgraph edge [Edge]
        traefik[Traefik]
    end

    subgraph identity [Identity]
        zitadel[Zitadel]
    end

    subgraph ui [Frontends - TypeScript / React]
        staffPortal[Staff portal<br/>SSOT admin + ticketing]
        customerPortal[Customer portal<br/>read-only view + tickets + self-service]
    end

    subgraph api [Services - Python / FastAPI]
        ssotApi[ssot-api]
        ticketApi[ticket-api]
        automationApi[automation-api]
    end

    subgraph data [Data]
        neo4j[(Neo4j<br/>identity + relationships)]
        postgres[(Postgres<br/>tickets, runs, JSONB text)]
    end

    subgraph later [Later]
        prefect[Prefect server]
        azure[Customer Azure tenants<br/>automation target only]
    end

    staff --> traefik
    customer --> traefik
    traefik --> staffPortal
    traefik --> customerPortal
    traefik --> ssotApi
    traefik --> ticketApi
    traefik --> automationApi

    staffPortal -. login .-> zitadel
    customerPortal -. login .-> zitadel
    ssotApi -. JWKS .-> zitadel
    ticketApi -. JWKS .-> zitadel
    automationApi -. JWKS .-> zitadel

    ssotApi --> neo4j
    ticketApi --> postgres
    automationApi --> postgres
    ticketApi -- edge stubs --> neo4j
    automationApi -. later .-> prefect
    prefect -. later .-> azure
```

## 2. Data ownership

Rule: every entity has exactly one home store. Other stores hold only its ID.

```mermaid
flowchart TB
    subgraph neo4j [Neo4j - what exists and how it relates]
        direction LR
        Customer --> Tenant
        Tenant --> Employee
        Employee --> EntraUser[Entra user]
        EntraUser --> Group
        Group --> IntunePackage[Intune package]
        Group --> Device
        Device --> TicketStub[Ticket stub<br/>id only]
    end

    subgraph postgres [Postgres - structured state and text]
        direction LR
        Ticket[Ticket<br/>columns: status, priority, requester_id, customer_id<br/>JSONB: body, comments, history]
        Run[Automation run<br/>columns: state, flow, ticket_id<br/>JSONB: params, log]
        Approval[Approval]
        Ticket --> Run
        Run --> Approval
    end

    Ticket -- after commit, write stub + edge --> TicketStub
```

Neo4j nodes carry: stable ID (ULID), name, type, minimal props needed for graph queries (e.g. Site lat/lon).
No bodies, no logs, no payloads.

## 3. Request flow: customer opens a ticket

```mermaid
sequenceDiagram
    actor C as Customer employee
    participant CP as Customer portal
    participant Z as Zitadel
    participant T as Traefik
    participant TA as ticket-api
    participant PG as Postgres
    participant SA as ssot-api
    participant N as Neo4j

    C->>CP: open portal
    CP->>Z: OIDC login
    Z-->>CP: JWT
    C->>CP: submit ticket about Device X
    CP->>T: POST /tickets (JWT)
    T->>TA: forward
    TA->>Z: JWKS (cached)
    TA->>SA: GET /nodes/{deviceId} validate exists + belongs to customer
    SA->>N: MATCH
    SA-->>TA: ok
    TA->>PG: INSERT ticket
    TA->>SA: POST /tickets/{id}/link device
    SA->>N: MERGE (:Ticket {id})-[:ABOUT]->(:Device)
    TA-->>CP: 201 ticket
```

## Open

- Component folder names and monorepo layout.
- Automation-api separate service or router inside ticket-api.
- Attachments store (MinIO) and mail (Mailpit) not drawn yet.