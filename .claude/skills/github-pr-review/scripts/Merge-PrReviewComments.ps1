#Requires -Version 7.0
<#
.SYNOPSIS
    Folds this round's AI review comments into the PR's canonical sonnet and opus comments.

.DESCRIPTION
    A PR keeps exactly one '## AI review - sonnet' and one '## AI review - opus' comment, forever.
    Per model, the lowest comment id is canonical; every higher-id AI comment is a duplicate a
    reviewer posted. Each duplicate is appended to the canonical comment's body as
    '### Round N - head <sha>' (header line and hidden head marker stripped) via PATCH, then the
    duplicate is deleted, then verified. The head in the round marker is the one embedded in the
    duplicate itself by Post-PrReview.ps1, so a leftover from an older round keeps its own sha;
    -HeadSha is only the fallback for comments posted without a marker. After each append a
    '**Latest:** round N (head <sha>) - <verdict>' line directly under the heading is inserted or
    replaced, so the headline never contradicts the newest round. Review wording is never changed.

    Always safe to run: a first round with nothing to merge is a reported no-op. Safe to re-run
    after a partial failure: a duplicate whose head marker and content already sit in the
    canonical body is not appended again, only deleted. Every verdict is validated before the
    first write, and a failure mid-way still prints the report of what landed.

.PARAMETER PrNumber
    GitHub pull request number in this repo.

.PARAMETER HeadSha
    PR head for this round. Used only for a duplicate that carries no embedded head marker.

.OUTPUTS
    JSON report per model: canonical id and url, rounds appended (with head), duplicates deleted,
    verification result, this round's verdict, error if the model's merge aborted.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][int]$PrNumber,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{7,40}$')][string]$HeadSha
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'GitHub.Common.ps1')

$fallbackSha = $HeadSha.Substring(0, 7).ToLower()
$comments    = @(Get-AiReviewComments -PrNumber $PrNumber)
$report      = [ordered]@{}

function Get-RoundMarker { param([int]$Round, [string]$Head) "### Round $Round - head ``$Head``" }

function Set-LatestLine {
    <# Inserts or replaces the '**Latest:**' line directly under the '## AI review' heading. #>
    param([string]$Body, [int]$Round, [string]$Head, [string]$Verdict)
    $line = "**Latest:** round $Round (head ``$Head``) - $Verdict"
    if ($Body -match '(?m)^\*\*Latest:\*\* .*$') {
        return [regex]::Replace($Body, '(?m)^\*\*Latest:\*\* .*$', $line, 1)
    }
    $parts = $Body -split "`r?`n", 2
    $parts[0] + "`n" + $line + "`n" + $parts[1]
}

foreach ($model in 'sonnet', 'opus') {
    $group = @($comments | Where-Object Model -eq $model | Sort-Object id)
    if ($group.Count -eq 0) { $report[$model] = @{ canonical = $null; note = 'no AI comment for this model' }; continue }

    $canonical = $group[0]
    $dupes     = @($group | Select-Object -Skip 1)
    $entry     = [ordered]@{
        canonical = $canonical.id
        url       = $canonical.html_url
        appended  = @()
        deleted   = @()
        verified  = $true
        verdict   = $null
        error     = $null
    }
    $report[$model] = $entry   # registered before any write so a failure still reports partial state

    try {
        $canonText = "$($canonical.body)".TrimEnd()
        $rounds    = [regex]::Matches($canonText, '(?m)^### Round \d+ - head').Count
        $verdict   = $null

        # Validate every duplicate before touching the PR.
        $work = foreach ($dupe in $dupes) {
            $content = "$($dupe.body)"
            $head    = Get-ReviewHead -Markdown $content
            if (-not $head) { $head = $fallbackSha }
            $stripped = $content -replace "^## AI review - $model[^\r\n]*\r?\n", ''
            $stripped = ($stripped -replace "\r?\n*$($script:AiReviewHeadPattern)\s*$", '').Trim()
            [pscustomobject]@{
                Dupe     = $dupe
                Head     = $head
                Verdict  = Get-ReviewVerdict -Markdown $content
                Stripped = $stripped
            }
        }

        foreach ($w in @($work)) {
            $verdict = $w.Verdict
            $alreadyMerged = $canonText.Contains("head ``$($w.Head)``") -and $canonText.Contains($w.Stripped)
            if ($alreadyMerged) {
                # Same head, same text: an earlier run appended it and failed on the delete.
                $entry.appended += @{ round = $null; head = $w.Head; from = $w.Dupe.id; note = 'already present in canonical comment' }
            } else {
                $round   = $rounds + 2
                $newBody = $canonText + "`n`n" + (Get-RoundMarker -Round $round -Head $w.Head) + "`n`n" + $w.Stripped
                $newBody = Set-LatestLine -Body $newBody -Round $round -Head $w.Head -Verdict $w.Verdict
                if ($newBody.Length -gt $script:GitHubCommentMaxLength) {
                    throw "Canonical comment $($canonical.id) would grow to $($newBody.Length) chars (max $script:GitHubCommentMaxLength) - duplicate $($w.Dupe.id) left in place."
                }
                $patched = Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/comments/$($canonical.id)") -Method PATCH -Body @{ body = $newBody }
                if (-not $patched.id) { throw "PATCH of canonical comment $($canonical.id) returned no id - duplicate $($w.Dupe.id) left in place." }
                $entry.appended += @{ round = $round; head = $w.Head; from = $w.Dupe.id }
                $canonText = $newBody
                $rounds++
            }

            Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/comments/$($w.Dupe.id)") -Method DELETE | Out-Null
            $entry.deleted += $w.Dupe.id
        }

        if ($verdict) { $entry.verdict = $verdict } else { $entry.note = 'nothing merged this round' }
    } catch {
        $entry.error    = $_.Exception.Message
        $entry.verified = $false
    }
}

# Verify: deleted duplicates now 404; canonical body carries every round marker (with its head)
# appended this run and the Latest line names the newest one. A failure here must not swallow
# the report of what already landed.
try {
    foreach ($model in 'sonnet', 'opus') {
        $entry = $report[$model]
        if (-not $entry.canonical -or $entry.error) { continue }
        $canon = Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/comments/$($entry.canonical)")
        $body  = "$($canon.body)"
        $last  = $null
        foreach ($a in $entry.appended) {
            if (-not $a.round) { continue }
            if (-not $body.Contains((Get-RoundMarker -Round $a.round -Head $a.head))) { $entry.verified = $false }
            $last = $a
        }
        if ($last -and -not $body.Contains("**Latest:** round $($last.round) (head ``$($last.head)``)")) { $entry.verified = $false }
        foreach ($id in $entry.deleted) {
            $gone = $false
            try { Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/comments/$id") | Out-Null } catch { if ($_.Exception.Message -match 'GitHub 404') { $gone = $true } }
            if (-not $gone) { $entry.verified = $false }
        }
    }
} catch {
    foreach ($model in 'sonnet', 'opus') {
        if ($report[$model].canonical) { $report[$model].verified = $null; $report[$model].verifyError = $_.Exception.Message }
    }
}

[pscustomobject]$report | ConvertTo-Json -Depth 6
if ($report.Values | Where-Object { $_.error }) { exit 1 }
