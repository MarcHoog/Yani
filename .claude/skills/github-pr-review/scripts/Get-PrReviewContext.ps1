#Requires -Version 7.0
<#
.SYNOPSIS
    Collects everything the AI reviewers need about a pull request, as one JSON object.

.DESCRIPTION
    Resolves head/base branches, fetches both, computes the merge base and PR head, lists the
    changed files, and checks whether the PR already carries AI review comments (which makes
    this a re-review that needs Merge-PrReviewComments.ps1 afterwards).

.PARAMETER PrNumber
    GitHub pull request number in this repo.

.EXAMPLE
    $ctx = .\Get-PrReviewContext.ps1 -PrNumber 12 | ConvertFrom-Json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][int]$PrNumber
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'GitHub.Common.ps1')

$repoRoot = Get-MainRepoRoot

$pr = Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/pulls/$PrNumber")
if (-not $pr.head.repo) { throw "PR #$PrNumber head repository no longer exists (deleted fork or repo) - nothing to review." }
if ($pr.head.repo.full_name -ne $pr.base.repo.full_name) {
    throw "PR #$PrNumber comes from a fork ($($pr.head.repo.full_name)) - fork PRs are not supported by this review flow."
}
$source = $pr.head.ref
$target = $pr.base.ref

git -C $repoRoot fetch --quiet origin $source $target
if ($LASTEXITCODE) { throw "git fetch origin $source $target failed ($LASTEXITCODE)." }

$mergeBase = git -C $repoRoot merge-base "origin/$target" "origin/$source"
if (-not $mergeBase) { throw "No merge base between origin/$target and origin/$source." }
$mergeBase = $mergeBase.Trim()
$head      = (git -C $repoRoot rev-parse "origin/$source").Trim()
if ($head -ne $pr.head.sha) { throw "origin/$source is at $head but GitHub reports PR head $($pr.head.sha) - fetch race, re-run." }
$files     = @(git -C $repoRoot diff --name-only $mergeBase "origin/$source")
$stat      = "$(git -C $repoRoot diff --shortstat $mergeBase "origin/$source")".Trim()

$aiComments = @(Get-AiReviewComments -PrNumber $PrNumber)

[pscustomobject]@{
    prNumber           = $PrNumber
    title              = $pr.title
    state              = $pr.state
    draft              = $pr.draft
    url                = $pr.html_url
    source             = $source
    target             = $target
    mergeBase          = $mergeBase
    head               = $head
    headShort          = $head.Substring(0, 7)
    shortStat          = $stat
    changedFiles       = $files
    hasPriorAiComment  = $aiComments.Count -gt 0
    aiComments         = @($aiComments | ForEach-Object { [pscustomobject]@{ id = $_.id; model = $_.Model; url = $_.html_url } })
    repoRoot           = $repoRoot
} | ConvertTo-Json -Depth 5
