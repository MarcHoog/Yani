---
name: poc-loop
description: One iteration of the yani mock-tenant POC loop - read docs/poc.md, pick the next open task, build it, verify it, commit, push, record progress, and stop at milestone gates for review. Run as `/loop /poc-loop` (self-paced) or `/poc-loop` for a single step. Use only when the user starts the POC loop.
---

# POC loop: one iteration

You are building the yani POC described in `docs\poc.md`: the full platform with real identity,
real databases and real services, where only the customer tenant is mocked behind the adapter
interfaces. Each invocation of this skill is one iteration: one task, verified, committed,
recorded. The state lives in `docs\poc.md`, not in your memory. Assume you remember nothing from
earlier iterations.

This skill is the user's explicit go-ahead to scaffold the component folders the task list
names (`automation-api\`, `customer-portal\`). It overrides the root `CLAUDE.md` rule "after
every push ask Next step?" for pushes inside a milestone; the question is asked only at a
milestone gate (step 7). Everything else in the root `CLAUDE.md` holds, the hard constraints
above all.

## 1. Orient

1. Read `docs\poc.md` in full. Read `CLAUDE.md`, and the `CLAUDE.md` of every component the next
   task touches. Read the `docs\architecture.md` section the task refers to.
2. `git status`, current branch, last commits.
3. Decide the state:
   - Status `waiting for review`: check whether the milestone PR is merged (github-pull-request
     skill). Not merged and the user did not say to continue: report that and stop the loop.
     Merged: branch the next milestone from fresh `main`, set status `in progress`.
   - Status `in progress` with uncommitted work: that is the current task, half done. Inspect the
     diff and finish it; do not start over.
   - Status `stopped`: report the reason recorded in the log and stop the loop.
4. Branch: if the session or the user names a branch, use it. Otherwise one branch per milestone,
   `poc/m<n>-<short-name>`, off `main`. Never commit to `main`.

## 2. Pick

Take the first unchecked task in the lowest open milestone that is not under Blocked. Write it
into Current (Task, and a Plan of 3 to 6 lines: files, endpoints, tests). Commit nothing yet.

If the task is too big for one iteration, split it in `docs\poc.md` into `a`, `b` sub-tasks and
take the first. If it needs a decision the Decisions section does not cover, take the option that
matches `docs\architecture.md` and the hard constraints, the smallest one if several do, and
record it under Decisions with one line of reasoning.

## 3. Build

- Smallest change that does the task. No extra abstractions, no work for later tasks.
- Port from the reference POC where it helps; never copy blindly, never modify it.
- The mock lives behind the adapter interface only. No `if mock:` anywhere else. No code path
  that exists only for the demo.
- Auth is never weakened to make something work: no bypass flags, no skipped token validation,
  no trusting `customer_id` from a URL or body for a customer token.
- Every new route that returns customer data gets a test that a customer token of customer B
  cannot read or change customer A's data.
- Generated TS clients are regenerated from OpenAPI, never hand-written.
- UI follows `docs\style.md` and `ui\CLAUDE.md`. New shared components go into `@yani/ui` with a
  story.

## 4. Verify

Run what applies and read the output. A task is done only when all of it passes.

- Python: `uv run ruff check` and `uv run ruff format --check` in each touched package,
  `python dev.py test`.
- TypeScript: typecheck and build of each touched package (`pnpm -r` scripts as the package
  defines them), `@yani/ui` tests when it changed.
- Stack: when compose, seed or a service changed, `python dev.py up` and `python dev.py seed`,
  then a smoke check against the running stack with a real Zitadel token (curl, or Playwright
  for UI). For UI tasks take a screenshot and look at it.
- From 6.1 on: `python dev.py e2e`.

If verification fails, fix it in this iteration. If you cannot, see Failure rules.

## 5. Record

Update `docs\poc.md`:

- Tick the task.
- Append to Log: `YYYY-MM-DD <task> <short sha> - verified: <what ran>; not verified: <what
  did not, and why>`. Be exact about what you did not check.
- Update Current (next task or `-`), Decisions, and Later (out-of-scope ideas you noticed).
- When a decision from Decisions is now real code, record it in `docs\architecture.md`.

## 6. Commit and push

Conventional commit messages, one commit per task (the `docs\poc.md` update in the same commit).
Push the milestone branch. If a PR for it exists, it updates; if not, and this is the first push
of the milestone, open it as a draft (github-pull-request skill) with the milestone's task list
in Remaining.

## 7. Gate or continue

- Milestone complete: update the PR body (Plan / Changes / Remaining), mark it ready for review,
  set Status `waiting for review`, commit and push that, end the loop, and ask the root
  `CLAUDE.md` "Next step?" question.
- Otherwise: end the iteration with a two-line summary (task done, next task). In a dynamic
  `/loop`, schedule the next iteration with a short delay (60 seconds); there is nothing external
  to wait for.

## Failure rules

- A task that fails verification at the end of an iteration: commit nothing broken. Stash or
  revert, note in the Log what failed and what you tried. Second failed iteration on the same
  task: move it to Blocked with the reason and the exact error, continue with the next task that
  does not depend on it.
- Three tasks Blocked, or the next task depends on a blocked one: set Status `stopped`, push the
  state, end the loop and tell the user what is blocked and what you need.
- Anything that would break a hard constraint in `CLAUDE.md`, or needs Microsoft/Google, or needs
  a credential you do not have: Blocked immediately, do not work around it.
- Never mark a task done that you did not verify. Never skip, disable or loosen a test to get
  green.
- The tooling for a check is missing (no Docker, no browser): record it as "not verified" in the
  Log, and do not tick tasks whose task text requires that check.
