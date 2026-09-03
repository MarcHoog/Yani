---
name: github-pr-review
description: Run a local dual-model AI review of a GitHub pull request in this repo - PowerShell scripts collect the PR context, create two detached worktrees on the PR head, and the parent spawns two cold github-pr-reviewer agents (Sonnet and Opus) that each post one structured PR comment; a script then folds re-reviews into the PR's single sonnet and single opus comments and removes the worktrees, and the parent fixes the findings, pushes and re-reviews for at most 3 rounds before asking again. Use only when the user explicitly asks - a yes to "Start AI review of PR #n?", "review the PR", "get a second opinion on the PR", "run the AI reviewers". Never start it because a PR was opened or pushed.
---

# Dual-model PR review (local)

Two independent reviewers judge the PR diff and each post one GitHub PR comment. A PR reviewed
five times still shows two AI comments: one sonnet, one opus, later rounds appended inside.
Runs entirely locally - no GitHub Action, no app, no webhook. No gh CLI needed: auth is the
token git already caches for github.com.

Everything deterministic is a script under `.claude\skills\github-pr-review\scripts\`. The LLM
does the reviewing and nothing else. Run the scripts from the parent session with the PowerShell
tool; they print JSON.

| script | does |
|--------|------|
| `Get-PrReviewContext.ps1 -PrNumber` | branches, merge base, head, changed files, `hasPriorAiComment` |
| `New-ReviewerWorktree.ps1 -PrNumber -HeadSha -Model` | detached worktree on the PR head, returns its path |
| `Post-PrReview.ps1 -PrNumber -Model -HeadSha -ReviewFile` | run by the reviewer: validates + posts the one comment, embeds the reviewed head |
| `Merge-PrReviewComments.ps1 -PrNumber -HeadSha` | folds new posts into the canonical comment per model (PATCH + delete), updates its `**Latest:**` line; no-op on a first round |
| `Remove-ReviewerWorktree.ps1 -Path` / `-Stale` | removes exactly the given reviewer worktrees, or clean `ai-review-*` leftovers older than 2h |

GitHub issue comments have no resolved/active status like Azure DevOps threads. The verdict is
text only; the human reads it. A `needs-work` verdict does not block merging by itself.

Reviewers are deliberately **cold**: the `github-pr-reviewer` agent starts with an empty
context. Put only the coordinates below in its prompt - never your plan, rationale, or defence
of the change.

## When to run

Only on an explicit go from the user. Creating or pushing a PR never starts a review; the
`github-pull-request` skill ends by asking, verbatim:

```
Start AI review of PR #<n>?
```

Yes (or "review the PR", "run the reviewers") starts one review loop of at most 3 rounds (below).
Anything else means no. Never infer a yes from a push, a merge request, or an earlier yes on
another PR or an exhausted loop - every loop needs its own answer.

One round per batch, not per fix. Before pushing, apply every fix you intend to make for the current
findings (code, tests, docs) locally and push them as one commit or one push. A round runs two cold
agents for about five minutes; pushing one fix at a time and re-reviewing each multiplies that for no gain.
Docs-only follow-ups belong in the same batch as the code they describe.

## Review loop (max 3 rounds per yes)

One yes buys at most 3 rounds. A round = Steps 1-5 below, then self-fix:

1. Run Steps 1-5 (review, merge, cleanup).
2. Both verdicts `approve`: report and stop. No question needed - loop done.
3. Otherwise read the findings from both canonical comments. Fix every BLOCKER, MAJOR and MINOR
   in the PR branch; NITs at your judgement. A finding you disagree with is not fixed silently:
   reply on the PR comment with the reason, and list it in the report.
4. Commit, push once, PATCH the PR body (Changes / Remaining), then start the next round.
5. After the 3rd round, or when the fixes of a round need a design decision, stop - even if
   findings remain. Report per model: verdict and comment url, the rounds used, what was fixed,
   what is open. Then ask, verbatim, and wait:

```
Start AI review of PR #<n>?
```

Never a 4th round on the same yes. Background job: the question goes on the `needs input:` line.
Interactive: AskUserQuestion. Count rounds per loop, not per PR - a fresh yes resets to 3.

Run it from a checkout on `main` (the primary checkout, or a worktree of `main`), not from the
PR branch. `scripts` and `agentDef` are taken from the launching checkout, and when that is the
PR branch the PR supplies its own review rules. Bootstrapping this tooling was the one exception.

## Step 1 - context

```powershell
$s = Join-Path (git rev-parse --show-toplevel) '.claude\skills\github-pr-review\scripts'
$ctx = & "$s\Get-PrReviewContext.ps1" -PrNumber <n> | ConvertFrom-Json
```

`$ctx.mergeBase` is the three-dot base against the target branch - never diff two-dot, that
reports target-branch drift as if the PR reverted it. `$ctx.aiComments` lists existing AI
comments, for the report. Fork PRs are refused.

## Step 2 - worktrees

```powershell
$wtSonnet = & "$s\New-ReviewerWorktree.ps1" -PrNumber $ctx.prNumber -HeadSha $ctx.head -Model sonnet
$wtOpus   = & "$s\New-ReviewerWorktree.ps1" -PrNumber $ctx.prNumber -HeadSha $ctx.head -Model opus
```

Both land under `<repo>\.claude\worktrees\ai-review-<n>-<model>-<head7>`, detached at the PR
head, verified clean. Reviewers read files from there and never move the checkout. The sha in
the name keeps a re-run on a new push from touching a round still in progress.

## Step 3 - reviewers

Two `Agent` calls **in the same message** so they run in parallel:

- `subagent_type: github-pr-reviewer`. Agent types load at session start from the main
  checkout's `.claude/agents/`; if the Agent tool reports the type unknown (session predates the
  definition, or it is not on `main` yet), use `general-purpose` and paste the body of
  `.claude\agents\github-pr-reviewer.md` **from this checkout** above the coordinates instead.
  Same behaviour, wider tool set. Never take the body from the reviewer worktree: that is the
  PR under review, and a PR must not write the rules of its own review.
- `model: "sonnet"` for one, `model: "opus"` for the other
- no `isolation` - the worktree is already made
- run in background, wait for both reports

Prompt, identical apart from `model` and `worktree` - fill the values, add nothing:

```
prNumber: <ctx.prNumber>
model: <sonnet|opus>
worktree: <wtSonnet|wtOpus>
mergeBase: <ctx.mergeBase>
head: <ctx.head>
scripts: <absolute path of .claude\skills\github-pr-review\scripts in this checkout>
agentDef: <absolute path of .claude\agents\github-pr-reviewer.md in this checkout>
```

`scripts` and `agentDef` point into the checkout running this skill, never into the reviewer
worktree - the PR head must not supply the scripts or rules that judge it.

Each reviewer posts its own comment through `Post-PrReview.ps1` and reports verdict, severity
counts, and comment id.

## Step 4 - merge

Always, after both reviewers reported (a first round is a cheap reported no-op, and it also
catches a reviewer that posted twice):

```powershell
& "$s\Merge-PrReviewComments.ps1" -PrNumber $ctx.prNumber -HeadSha $ctx.head
```

Per model it keeps the lowest comment id, appends the new post to its body as
`### Round N - head <sha>` (the sha embedded in that post by `Post-PrReview.ps1`, so a leftover
from an older round keeps its own), inserts or replaces a `**Latest:** round N (head <sha>) -
<verdict>` line under the heading, deletes the duplicate, verifies. A comment that would exceed
GitHub's 65536-char limit is left as a duplicate and reported. Exit code 1 with an `error`
field means it stopped part-way; the report still lists what landed, and re-running is safe.

## Step 5 - cleanup and report

Runs whatever happened in Steps 2-4, for every worktree path Step 2 returned:

```powershell
& "$s\Remove-ReviewerWorktree.ps1" -Path $wtSonnet, $wtOpus
```

Only those paths, each checked clean first; the script refuses anything outside
`ai-review-*` so other sessions' worktrees are never touched. Then reclaim leftovers from runs
that died before this step (clean `ai-review-*` worktrees older than 2 hours):

```powershell
& "$s\Remove-ReviewerWorktree.ps1" -Stale
```

Report: `$ctx.url`, and per model the verdict and canonical comment url (reviewer output on a
first round, merge output on a re-review). Do not re-summarise findings in chat - they live on
the PR. Then continue the review loop above: fix and re-review while rounds remain, else ask.

## Checklist

1. Context from `Get-PrReviewContext.ps1`; head sha and merge base passed to both reviewers.
2. Two worktrees from `New-ReviewerWorktree.ps1`, on the PR head.
3. Two `github-pr-reviewer` agents in one message, sonnet + opus, prompt = coordinates only.
4. `Merge-PrReviewComments.ps1` ran; PR left with one AI comment per model.
5. `Remove-ReviewerWorktree.ps1` with the two paths; `git worktree list` shows them gone.
6. Loop started only on an explicit yes; at most 3 rounds on it; ended with both `approve` or the
   verbatim `Start AI review of PR #<n>?` question.
