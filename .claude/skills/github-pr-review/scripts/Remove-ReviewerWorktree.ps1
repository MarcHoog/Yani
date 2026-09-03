#Requires -Version 7.0
<#
.SYNOPSIS
    Removes reviewer worktrees created by New-ReviewerWorktree.ps1 - by exact path, or stale ones.

.DESCRIPTION
    -Path: each path must be a registered ai-review-* worktree with no local changes; anything
    else is skipped and reported, never forced.
    -Stale: every registered ai-review-* worktree under <repo>\.claude\worktrees older than
    -OlderThanHours (default 2) and clean is removed - the reclaim path for runs whose parent
    session died before cleanup. A round in progress is younger than that and untouched.
    Other sessions run their own worktrees under the same directory - this never sweeps outside
    the ai-review-* name, never by wildcard beyond it, and never prunes. Reviewer worktrees are
    detached, so there is no branch to delete.

.OUTPUTS
    JSON: removed and skipped paths with reasons.
#>
[CmdletBinding(DefaultParameterSetName = 'Path')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Path')][string[]]$Path,
    [Parameter(Mandatory, ParameterSetName = 'Stale')][switch]$Stale,
    [Parameter(ParameterSetName = 'Stale')][double]$OlderThanHours = 2
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'GitHub.Common.ps1')

$repoRoot   = Get-MainRepoRoot
$registered = @(Get-RegisteredWorktrees -RepoRoot $repoRoot)
$pattern    = Join-Path $repoRoot '.claude' 'worktrees' 'ai-review-*'

if ($Stale) {
    $cutoff = (Get-Date).AddHours(-$OlderThanHours)
    # A registered worktree whose directory is already gone is the classic leftover: always stale.
    $Path = @($registered | Where-Object { $_ -like $pattern -and (-not (Test-Path $_) -or (Get-Item $_).CreationTime -lt $cutoff) })
}

$removed = @(); $skipped = @()
foreach ($p in $Path) {
    $full = [IO.Path]::GetFullPath($p).TrimEnd('\')
    if ($registered -notcontains $full) { $skipped += @{ path = $full; reason = 'not a registered worktree' }; continue }
    if ($full -notlike $pattern) { $skipped += @{ path = $full; reason = 'not an ai-review worktree' }; continue }
    if ((Test-Path $full) -and (git -C $full status --porcelain)) { $skipped += @{ path = $full; reason = 'local changes' }; continue }
    git -C $repoRoot worktree remove $full --force
    if ($LASTEXITCODE) { $skipped += @{ path = $full; reason = "git worktree remove failed ($LASTEXITCODE)" }; continue }
    $removed += $full
}
# No `git worktree prune`: it is repo-wide and would unregister other sessions' worktrees.

[pscustomobject]@{ mode = $PSCmdlet.ParameterSetName; removed = $removed; skipped = $skipped } | ConvertTo-Json -Depth 4
