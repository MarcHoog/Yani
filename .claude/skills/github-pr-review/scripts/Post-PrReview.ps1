#Requires -Version 7.0
<#
.SYNOPSIS
    Posts one AI review as a single top-level PR comment.

.DESCRIPTION
    Reads the review markdown from -ReviewFile (never from a here-string - review text quotes
    PowerShell and "$var" would expand), validates the header, verdict and length, then POSTs one
    issue comment on the PR. GitHub issue comments carry no status, so the verdict lives in the
    text only. The reviewed head sha is appended as a hidden HTML comment so a later merge can
    label the round with the head it was actually written against. The review file is deleted
    after a successful post, and a file older than an hour is refused, so a later round cannot
    post a leftover.

.PARAMETER PrNumber
    GitHub pull request number in this repo.

.PARAMETER Model
    Reviewer label; the file's first line must be '## AI review - <Model>'.

.PARAMETER ReviewFile
    Path of the review markdown written by the reviewer.

.PARAMETER HeadSha
    PR head the review was written against - from the reviewer's prompt.

.OUTPUTS
    JSON: prNumber, model, commentId, url, verdict, head.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][int]$PrNumber,
    [Parameter(Mandatory)][ValidateSet('sonnet', 'opus')][string]$Model,
    [Parameter(Mandatory)][string]$ReviewFile,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{7,40}$')][string]$HeadSha
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'GitHub.Common.ps1')

if (-not (Test-Path $ReviewFile)) { throw "Review file not found: $ReviewFile" }
$age = (Get-Date) - (Get-Item $ReviewFile).LastWriteTime
if ($age.TotalMinutes -gt 60) { throw "Review file $ReviewFile was written $([int]$age.TotalMinutes) min ago - stale; write this round's review first." }
$markdown = "$(Get-Content -Path $ReviewFile -Raw -Encoding utf8)".TrimEnd()
if (-not $markdown) { throw "Review file is empty: $ReviewFile" }

$firstLine = ($markdown -split "`r?`n", 2)[0].Trim()
if ($firstLine -ne "## AI review - $Model") {
    throw "First line must be exactly '## AI review - $Model', got '$firstLine'."
}
$verdict = Get-ReviewVerdict -Markdown $markdown
if ($markdown -match $script:AiReviewHeadPattern) { throw 'Review file already carries an ai-review head marker - the script adds it, do not write it yourself.' }
$shortSha = $HeadSha.Substring(0, 7).ToLower()
$markdown = $markdown + "`n`n<!-- ai-review head:$shortSha -->"
# Checked after the marker so the length tested is the length posted.
if ($markdown.Length -gt $script:GitHubCommentMaxLength) { throw "Review is $($markdown.Length) chars incl. head marker; GitHub comments max $script:GitHubCommentMaxLength. Trim the findings." }

$comment = Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/$PrNumber/comments") -Method POST -Body @{ body = $markdown }
if (-not $comment.id) { throw 'GitHub returned no comment id.' }
Remove-Item -Path $ReviewFile -Force   # posted; a stale file must not be picked up by a later round

[pscustomobject]@{
    prNumber  = $PrNumber
    model     = $Model
    commentId = $comment.id
    url       = $comment.html_url
    verdict   = $verdict
    head      = $shortSha
} | ConvertTo-Json
