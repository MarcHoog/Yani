# yani vision

What yani is, for whom, and what it deliberately is not. Technical design lives in
`docs\architecture.md`, build order in `docs\roadmap.md`.

## In one paragraph

Yani is a managed layer on top of Microsoft 365 (and later Google Workspace) for small and
medium businesses. It does to an SMB tenant what an opinionated cloud platform does to raw
virtual machines: fewer knobs, one safe way of doing every common thing, heavy automation, at a
small markup. A shared mailbox, a new employee, a laptop, a group: yani always builds it the
same way, our standard, and keeps it that way. The customer sees what they have, what it costs
and whether it is healthy. They ask for changes through forms. We run the changes.

## The problem

- SMBs run Microsoft 365 or Google Workspace with nobody who really owns it. Every admin, intern
  or external party clicked things together differently.
- Security depends on settings nobody remembers making: MFA exceptions, licensed shared
  mailboxes, stale accounts of people who left, devices outside Intune.
- Nobody can say what the licenses cost per person, which are unused, or why the bill went up.
- Doing it properly takes knowledge of Entra, Exchange, Intune and licensing that the business
  does not have and does not want.

## The product

### Roles

| role | who | can |
|---|---|---|
| Operator | us (the service provider) | everything: see all customers, approve and run changes, manage standards and forms, fix drift |
| Customer | a contact at the SMB | see their own tenant read-only, fill in published forms, follow their requests |

The customer never gets write access to anything directly. Every change goes through a form, and
every form goes through a standard.

### What the customer sees

A small, calm, read-only overview of their own tenant:

- People: users, what they have access to, which device they use, which license they hold.
- Shared mailboxes, groups and teams, with their members.
- Devices and whether they are managed and compliant.
- Licenses and cost: what is assigned, what is unused, cost per person and per department, the
  monthly total and what changed.
- Health: where the tenant does not match the standard, in plain words.
- Their requests and the status of each.

### Forms

Forms are the only way a customer asks for something. We publish a fixed set per customer, for
example:

- New employee
- Employee leaves
- Shared mailbox
- New or replacement device
- Access change (add or remove someone from a mailbox or group)
- License change

A form asks for business facts ("Jan Peeters, Sales, starts 1 December, needs a laptop"), never
for technical choices. Validation happens on the form, before anything reaches us.

### Standards

Behind every form sits a standard: our one way of doing that thing. A standard turns the form's
answers into a concrete plan, for example for a shared mailbox:

- naming convention and address
- no license, sign-in blocked
- access through a security group, never direct permissions
- an owner who approves future access
- auditing on

Standards are data, versioned, and the same for every customer unless we deliberately allow a
variant. The same standards define what "healthy" means for the drift checks.

### Plan, approve, apply

Every request becomes a plan before it becomes a change: what will be created, changed or removed,
and what it does to the monthly cost. The operator approves (low-risk forms can auto-approve), the
plan is applied, and every step is logged. The customer sees the result.

### Drift

People will still click around in the admin centers. Yani syncs every tenant on a schedule,
compares it to the standards and shows the differences, to the operator as work and to the
customer as plain-language health. Fixing drift is the same plan-and-apply flow as a request.

## Principles

1. **One way per thing.** If there are two ways to make a shared mailbox, one of them is wrong.
2. **Read-only by default.** Customers look and ask; they do not touch.
3. **Plan before change.** Nothing runs that was not shown first, including its cost.
4. **Everything is logged.** Who asked, who approved, what ran, what it returned.
5. **Plain language.** The customer sees "Jan can read the invoices mailbox", not a permission ID.
6. **Dumb on purpose.** Missing flexibility is a feature. A request that does not fit a form is a
   conversation, not a new knob.

## Not in scope

- A general admin center replacement. Operators still use the Microsoft admin centers for the odd
  case; yani then shows it as drift until it is folded into a standard.
- Self-service writes for customers.
- Helpdesk ticketing beyond requests (no phone, no free-text tickets in the first version).
- Billing and invoicing the customer. Yani shows cost; invoicing stays elsewhere for now.
- Google Workspace in the first version. The adapter boundary is designed for it; the
  implementation comes after Microsoft 365 works end to end.
