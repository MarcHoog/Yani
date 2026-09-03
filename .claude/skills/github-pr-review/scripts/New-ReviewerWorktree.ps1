#Requires -Version 7.0
<#
.SYNOPSIS
    Creates a detached git worktree at the PR head for one AI reviewer.

.DESCRIPTION
    Worktree lands under <main repo>\.claude\worktrees\ai-review-<PrNumber>-<Model>-<head7>,
    checked out detached at -HeadSha, so the reviewer reads the PR version of every file straight
    from disk and never has to move the checkout itself. A leftover worktree from an aborted run
    at the same head is removed first when it is clean; a dirty one aborts.

.PARAMETER HeadSha
    Commit the worktree is detached at - the PR head from Get-PrReviewContext.ps1.

.PARAMETER Model
    Reviewer label (sonnet|opus), used only to name the path.

.OUTPUTS
    The worktree path.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][int]$PrNumber,
    [Parameter(Mandatory)][string]$HeadSha,
    [Parameter(Mandatory)][ValidateSet('sonnet', 'opus')][string]$Model
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'GitHub.Common.ps1')

$repoRoot = Get-MainRepoRoot

$resolved = git -C $repoRoot rev-parse --verify --quiet "$HeadSha^{commit}"
if (-not $resolved) { throw "HeadSha '$HeadSha' does not resolve to a commit - run Get-PrReviewContext.ps1 first so it is fetched." }
$HeadSha = $resolved.Trim()

# Head sha in the name: a re-run on a new push never shares a path with a round still reviewing.
$path = Join-Path $repoRoot '.claude' 'worktrees' "ai-review-$PrNumber-$Model-$($HeadSha.Substring(0, 7))"

if ((Get-RegisteredWorktrees -RepoRoot $repoRoot) -contains $path) {
    if (git -C $path status --porcelain) { throw "Stale reviewer worktree at $path has local changes - not removing it." }
    git -C $repoRoot worktree remove $path --force
    if ($LASTEXITCODE) { throw "git worktree remove $path failed ($LASTEXITCODE)." }
} elseif (Test-Path $path) {
    throw "Path $path exists but is not a registered worktree - remove it manually."
}

git -C $repoRoot worktree add --quiet --detach $path $HeadSha
if ($LASTEXITCODE) { throw "git worktree add $path $HeadSha failed ($LASTEXITCODE)." }

$actual  = "$(git -C $path rev-parse HEAD)".Trim()
$problem = if ($actual -ne $HeadSha) { "Worktree HEAD $actual does not match requested $HeadSha." }
           elseif (git -C $path status --porcelain) { "Fresh worktree at $path is not clean." }
if ($problem) {
    git -C $repoRoot worktree remove $path --force   # do not leak a registered worktree the caller never learned about
    throw $problem
}

$path
