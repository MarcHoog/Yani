---
name: github-pull-request
description: Interact with GitHub via PowerShell REST - pull requests (clean feature-branch flow, conventional-commit titles, Plan/Changes/Remaining body), Actions runs and check results, and issues. Use whenever asked to open/update/resume a PR, check CI status or logs, or read/link issues in this repo (yani). No gh CLI needed - auth is the token git already caches for github.com.
---

# GitHub Pull Requests

How to open and maintain pull requests in this repo cleanly. PowerShell REST only; `gh` is not
installed and not required.

Repo coordinates are derived from the origin remote by `GitHub.Common.ps1`
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

Auth and the REST wrapper live in `.claude\skills\github-pr-review\scripts\GitHub.Common.ps1` -
dot-source it. `Invoke-GitHub -Uri -Method -Body` takes a path (`/repos/...`) or full URL and
throws on non-2xx with GitHub's message. `Get-GitHubRepoPath` prefixes `/repos/<owner>/<repo>`.

```powershell
. (Join-Path (git rev-parse --show-toplevel) '.claude\skills\github-pr-review\scripts\GitHub.Common.ps1')
```

## Create a PR

Body via a file or single-quoted here-string - PR bodies quote code and `"$var"` expands.

```powershell
$branch = git branch --show-current
$body = @'
## Plan
<what was planned and why>

## Changes
- <change 1>
- <change 2>

## Remaining
None
'@

$pr = Invoke-GitHub (Get-GitHubRepoPath '/pulls') POST @{
    title = '<type(scope): summary>'
    head  = $branch
    base  = 'main'
    body  = $body
    draft = $false   # $true for work in progress
}
Write-Host "PR #$($pr.number): $($pr.html_url)"
```

## After creating (or updating) a PR

Never launch the AI review on your own. After every PR create or push, report the PR url and ask
the user this question verbatim, then stop and wait for the answer:

```
Start AI review of PR #<n>?
```

Background job: put it on the `needs input:` line. Interactive: AskUserQuestion. Only an explicit
yes starts the `github-pr-review` skill - "review it", "run the reviewers", "yes" all count; silence,
a different task, or a push alone never do. The review skill owns the loop from there (max 3
review + self-fix rounds per yes, then it asks the same question again).

Batch before you push: address all current findings and related docs locally, then push once. Every
push costs one full review round, so one fix per push is the wrong cadence.

## List open PRs

```powershell
$prs = Invoke-GitHub (Get-GitHubRepoPath '/pulls?state=open')
$prs | ForEach-Object { "#$($_.number): $($_.title) [$($_.head.ref)]$(if ($_.draft) { ' (draft)' })" }
```

## Get PR details (read before resuming)

```powershell
$pr = Invoke-GitHub (Get-GitHubRepoPath '/pulls/{n}')
$pr.body
```

## Update PR body (multi-session continuity)

```powershell
Invoke-GitHub (Get-GitHubRepoPath '/pulls/{n}') PATCH @{ body = $updatedBody }
```

## Add a PR comment

```powershell
Invoke-GitHub (Get-GitHubRepoPath '/issues/{n}/comments') POST @{ body = '<comment>' }
```

## Mark ready / convert to draft

Ready-for-review has no REST endpoint; use the GitHub UI. Draft flag can only be set at creation via REST.

## Actions / checks

Latest workflow runs for a branch:

```powershell
$runs = (Invoke-GitHub (Get-GitHubRepoPath "/actions/runs?branch=$branch&per_page=5")).workflow_runs
$runs | ForEach-Object { "$($_.id): $($_.name) - $($_.status) ($($_.conclusion))" }
```

Check runs for the PR head commit:

```powershell
$checks = (Invoke-GitHub (Get-GitHubRepoPath "/commits/$($pr.head.sha)/check-runs")).check_runs
$checks | ForEach-Object { "$($_.name): $($_.status) ($($_.conclusion))" }
```

Log of the failed job (endpoint redirects to plain text; `Invoke-WebRequest` follows it):

```powershell
$jobs = (Invoke-GitHub (Get-GitHubRepoPath "/actions/runs/{runId}/jobs")).jobs
$job  = $jobs | Where-Object conclusion -eq 'failure' | Select-Object -First 1
Invoke-WebRequest -Uri "https://api.github.com$(Get-GitHubRepoPath "/actions/jobs/$($job.id)/logs")" -Headers (Get-GitHubHeaders) -OutFile "$env:TEMP\job-log.txt"
```

Whole run as zip: `/actions/runs/{runId}/logs`.

## Issues

Get an issue:

```powershell
$issue = Invoke-GitHub (Get-GitHubRepoPath '/issues/{n}')
"#$($issue.number): $($issue.title) [$($issue.state)]"
```

Link an issue to the PR: put `Closes #<n>` (or `Refs #<n>` without auto-close) in the PR body.
GitHub links it automatically; no API call needed.

## Checklist

1. On a feature branch (not `main`), targeting `main`.
2. Changes committed and pushed.
3. PR created with a conventional `type(scope): summary` title and the Plan / Changes / Remaining body.
4. Issue referenced in the body if one exists.
5. On resume: body PATCHed with latest progress.
6. After the push: asked `Start AI review of PR #<n>?` verbatim and stopped. Review launched only on an explicit yes.
