---
name: github-pull-request
description: Interact with GitHub via Python REST - pull requests (clean feature-branch flow, conventional-commit titles, Plan/Changes/Remaining body), Actions runs and check results, and issues. Use whenever asked to open/update/resume a PR, check CI status or logs, or read/link issues in this repo (yani). No gh CLI needed - auth is the token git already caches for github.com. Cross-platform: any OS with python3.
---

# GitHub Pull Requests

How to open and maintain pull requests in this repo cleanly. Python REST only; `gh` is not
installed and not required. Scripts are stdlib-only Python 3.10+ and run on any OS.

Repo coordinates are derived from the origin remote by `github_common.py`
(`https://github.com/<owner>/<repo>.git`). Target branch is always `main`.

## Rules (non-negotiable)

- Feature branch before any change. Never commit to `main` directly.
- Branch off `main` and target `main`.
- PR title is a conventional-commit line (see "PR title" below) - it becomes the squash-merge
  commit subject.
- PR body always uses the Plan / Changes / Remaining format below so another session can pick up cold.
- When resuming an existing PR: read its body first, then PATCH the body with progress before ending the session.
- Commit and push when the user asks, or when running as a background job whose work must survive
  the session. Then open the PR.

## PR title (conventional commits)

Format: `type(scope): summary` - always, for every PR in this repo.

| type | use for |
|------|---------|
| `feat` | new capability, new endpoint, new component |
| `fix` | bug fix |
| `chore` | tooling, deps, config, repo hygiene |
| `docs` | docs and diagrams only |
| `refactor` | no behaviour change |
| `ci` | GitHub Actions and checks |
| `test` | tests only |

Scope = the component folder touched (`ssot-api`, `ticket-api`, `staff-portal`,
`customer-portal`, `py-core`, `ui`, `infra`, `docs`, `claude` for agent/skill tooling). Multi-area
PRs: pick the dominant one. Append `!` after the scope for a breaking API contract change.

## PR body format

```
## Plan
<what was planned and why>

## Changes
<bullet list of what changed>

## Remaining
<anything left to do, or "None">
```

## Setup

Everything goes through `gh_api.py` in `.claude/skills/github-pr-review/scripts/`. It takes a
method and a path (repo-relative like `pulls`, absolute like `/repos/...`, or a full
api.github.com URL) and prints the JSON response. `--body-file <json>` for POST/PATCH bodies,
`--paginate` for long lists, `--download <file>` for raw payloads like job logs. Non-2xx exits 1
with GitHub's message on stderr.

```bash
S="$(git rev-parse --show-toplevel)/.claude/skills/github-pr-review/scripts"
```

## Create a PR

Body via a JSON file written with the Write tool - PR bodies quote code and shell strings
mangle it. Never build the JSON inline in the shell.

`pr.json` (in the scratchpad or temp dir):

```json
{
  "title": "<type(scope): summary>",
  "head": "<branch>",
  "base": "main",
  "draft": false,
  "body": "## Plan\n<what was planned and why>\n\n## Changes\n- <change 1>\n- <change 2>\n\n## Remaining\nNone"
}
```

```bash
python3 "$S/gh_api.py" POST pulls --body-file pr.json
```

The response carries `number` and `html_url`.

## After creating (or updating) a PR

Never launch the AI review on your own. After every PR create or push, report the PR url and ask
what to do next, then stop and wait for the answer. Interactive: AskUserQuestion. Background job:
the question and options go on the `needs input:` line. The question names the PR and offers
exactly these choices (AskUserQuestion adds "Other" by itself; a background job lists it):

```
PR #<n> ready: <url>. Next step?
- Review with 2 agents (Sonnet + Opus dual review)
- Review with 1 agent (Opus only, faster)
- Resolve comments (read PR feedback and address it)
- Make more changes
- PR merged - clear worktree
- Other
```

AskUserQuestion caps at 4 custom options ("Other" is added automatically): interactive
sessions offer 2 agents / 1 agent / resolve comments / merged-clear, and "make more changes"
arrives as free text via Other. A background job lists all six.

Routing:

- **Review with 2 agents / 1 agent** - start the `github-pr-review` skill with that agent count.
  Only an explicit review answer starts it - one of these options, or the user's own words
  ("review it", "run the reviewers" = 2 agents unless they say otherwise); silence, a different
  task, or a push alone never do. The review skill owns the loop from there (max 3 review +
  self-fix rounds per answer, then it asks this question again).
- **Resolve comments** - read the PR's feedback with the `github-pr-comments` skill, address it,
  push once, then ask this question again.
- **Make more changes / Other** - do what the user says; after the next push, ask again.
- **PR merged - clear worktree** - clean up after the merge, never perform the merge itself.
  First confirm: `gh_api.py GET pulls/<n>` must show `"merged": true` - if not, report that and
  ask again. Then from the main checkout: `git fetch --prune origin`, delete the local feature
  branch (`git branch -d <branch>` - `-d`, never `-D`; an unmerged error is a finding to report),
  and remove the feature worktree (`git -C <mainRoot> worktree remove <path>`) if the work lives
  in one. Never force-remove a dirty worktree - report the leftover changes instead. Removing
  the worktree the session itself runs in deletes its own cwd: make it the very last action and
  say so in the report.

Batch before you push: address all current findings and related docs locally, then push once. Every
push costs one full review round, so one fix per push is the wrong cadence.

## List open PRs

```bash
python3 "$S/gh_api.py" GET "pulls?state=open"
```

## Get PR details (read before resuming)

```bash
python3 "$S/gh_api.py" GET pulls/<n>
```

Read `.body` from the output.

## Update PR body (multi-session continuity)

Write `body.json` as `{"body": "<updated markdown>"}` with the Write tool, then:

```bash
python3 "$S/gh_api.py" PATCH pulls/<n> --body-file body.json
```

## Add a PR comment

```bash
python3 "$S/gh_api.py" POST issues/<n>/comments --body-file comment.json
```

with `comment.json` as `{"body": "<comment markdown>"}`. To read the comments already on a PR
(human feedback, review verdicts, inline threads), use the `github-pr-comments` skill.

## Mark ready / convert to draft

Ready-for-review has no REST endpoint; use the GitHub UI. Draft flag can only be set at creation via REST.

## Actions / checks

Latest workflow runs for a branch:

```bash
python3 "$S/gh_api.py" GET "actions/runs?branch=<branch>&per_page=5"
```

Read `.workflow_runs[]` - `id`, `name`, `status`, `conclusion`.

Check runs for the PR head commit:

```bash
python3 "$S/gh_api.py" GET commits/<headSha>/check-runs
```

Log of a failed job (`.jobs[]` from the runs endpoint, pick `conclusion == "failure"`):

```bash
python3 "$S/gh_api.py" GET actions/runs/<runId>/jobs
python3 "$S/gh_api.py" GET actions/jobs/<jobId>/logs --download job-log.txt
```

Whole run as zip: `actions/runs/<runId>/logs --download run-logs.zip`.

## Issues

Get an issue:

```bash
python3 "$S/gh_api.py" GET issues/<n>
```

Link an issue to the PR: put `Closes #<n>` (or `Refs #<n>` without auto-close) in the PR body.
GitHub links it automatically; no API call needed.

## Checklist

1. On a feature branch (not `main`), targeting `main`.
2. Changes committed and pushed.
3. PR created with a conventional `type(scope): summary` title and the Plan / Changes / Remaining body.
4. Issue referenced in the body if one exists.
5. On resume: body PATCHed with latest progress.
6. After the push: asked the "Next step?" question (2 agents / 1 agent / resolve comments / more changes / merged-clear / other) and stopped. Review launched only on an explicit review answer.
