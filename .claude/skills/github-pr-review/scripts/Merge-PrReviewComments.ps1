#Requires -Version 7.0
<#
.SYNOPSIS
    Folds this round's AI review comments into the PR's canonical sonnet and opus comments.

.DESCRIPTION
    A PR keeps exactly one '## AI review - sonnet' and one '## AI review - opus' comment, forever.
    Per model, the lowest comment id is canonical; every higher-id AI comment is a duplicate the
    reviewer just posted. Each duplicate is appended to the canonical comment's body as
    '### Round N - head <sha>' (header line stripped) via PATCH, then the duplicate is deleted,
    then verified. Review wording is never changed.

    Always safe to run: a first round with nothing to merge is a reported no-op. Safe to re-run
    after a partial failure: a duplicate whose round marker (this head) and content already sit
    in the canonical body is not appended again, only deleted. Every verdict is validated before
    the first write, and a failure mid-way still prints the report of what landed.

.PARAMETER HeadSha
    PR head for this round - stamped into the round marker.

.OUTPUTS
    JSON report per model: canonical id and url, rounds appended, duplicates deleted,
    verification result, this round's verdict, error if the model's merge aborted.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][int]$PrNumber,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{7,40}$')][string]$HeadSha
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'GitHub.Common.ps1')

$shortSha = $HeadSha.Substring(0, 7).ToLower()
$marker   = "### Round {0} - head ``$shortSha``"
$comments = @(Get-AiReviewComments -PrNumber $PrNumber)
$report   = [ordered]@{}

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
            [pscustomobject]@{
                Dupe     = $dupe
                Verdict  = Get-ReviewVerdict -Markdown $content
                Stripped = ($content -replace "^## AI review - $model[^\r\n]*\r?\n", '').Trim()
            }
        }

        foreach ($w in @($work)) {
            $verdict = $w.Verdict
            $alreadyMerged = $canonText.Contains("head ``$shortSha``") -and $canonText.Contains($w.Stripped)
            if ($alreadyMerged) {
                # Same head, same text: an earlier run appended it and failed on the delete.
                $entry.appended += @{ round = $null; from = $w.Dupe.id; note = 'already present in canonical comment' }
            } else {
                $round   = $rounds + 2
                $newBody = $canonText + "`n`n" + ($marker -f $round) + "`n`n" + $w.Stripped
                if ($newBody.Length -gt $script:GitHubCommentMaxLength) {
                    throw "Canonical comment $($canonical.id) would grow to $($newBody.Length) chars (max $script:GitHubCommentMaxLength) - duplicate $($w.Dupe.id) left in place."
                }
                $patched = Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/comments/$($canonical.id)") -Method PATCH -Body @{ body = $newBody }
                if (-not $patched.id) { throw "PATCH of canonical comment $($canonical.id) returned no id - duplicate $($w.Dupe.id) left in place." }
                $entry.appended += @{ round = $round; from = $w.Dupe.id }
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

# Verify: deleted duplicates now 404; canonical body carries every round marker appended this run.
# A failure here must not swallow the report of what already landed.
try {
    foreach ($model in 'sonnet', 'opus') {
        $entry = $report[$model]
        if (-not $entry.canonical -or $entry.error) { continue }
        $canon = Invoke-GitHub -Uri (Get-GitHubRepoPath -Path "/issues/comments/$($entry.canonical)")
        foreach ($a in $entry.appended) {
            if ($a.round -and -not "$($canon.body)".Contains(($marker -f $a.round))) { $entry.verified = $false }
        }
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
