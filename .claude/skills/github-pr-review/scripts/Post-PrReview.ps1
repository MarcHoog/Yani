#Requires -Version 7.0
<#
.SYNOPSIS
    Posts one AI review as a single top-level PR comment.

.DESCRIPTION
    Reads the review markdown from -ReviewFile (never from a here-string - review text quotes
    PowerShell and "$var" would expand), validates the header, verdict and length, then POSTs one
    issue comment on the PR. GitHub issue comments carry no status, so the verdict lives in the
    text only. The review file is deleted after a successful post, and a file older than an hour
    is refused, so a later round cannot post a leftover.

.PARAMETER Model
    Reviewer label; the file's first line must be '## AI review - <Model>'.

.OUTPUTS
    JSON: commentId, url, verdict.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][int]$PrNumber,
    [Parameter(Mandatory)][ValidateSet('sonnet', 'opus')][string]$Model,
    [Parameter(Mandatory)][string]$ReviewFile
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'GitHub.Common.ps1')

if (-not (Test-Path $ReviewFile)) { throw "Review file not found: $ReviewFile" }
$age = (Get-Date) - (Get-Item $ReviewFile).LastWriteTime
if ($age.TotalMinutes -gt 60) { throw "Review file $ReviewFile was written $([int]$age.TotalMinutes) min ago - stale; write this round's review first." }
$markdown = "$(Get-Content -Path $ReviewFile -Raw -Encoding utf8)".TrimEnd()
if (-not $markdown) { throw "Review file is empty: $ReviewFile" }
if ($markdown.Length -gt $script:GitHubCommentMaxLength) { throw "Review is $($markdown.Length) chars; GitHub comments max $script:GitHubCommentMaxLength. Trim the findings." }

$firstLine = ($markdown -split "`r?`n", 2)[0].Trim()
if ($firstLine -ne "## AI review - $Model") {
    throw "First line must be exactly '## AI review - $Model', got '$firstLine'."
}
$verdict = Get-ReviewVerdict -Markdown $markdown

$comment = Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/$PrNumber/comments") -Method POST -Body @{ body = $markdown }
if (-not $comment.id) { throw 'GitHub returned no comment id.' }
Remove-Item -Path $ReviewFile -Force   # posted; a stale file must not be picked up by a later round

[pscustomobject]@{
    prNumber  = $PrNumber
    model     = $Model
    commentId = $comment.id
    url       = $comment.html_url
    verdict   = $verdict
} | ConvertTo-Json
