#Requires -Version 7.0
<#
.SYNOPSIS
    Shared helpers for the github-pr-review scripts. Dot-source, do not run.

.DESCRIPTION
    Repo coordinates (derived from the origin remote), authenticated GitHub REST wrapper, and
    AI-review comment discovery for pull requests. Auth uses the token git's credential helper
    already caches for github.com (the same one that lets you push). No gh CLI required.
#>

$script:GitHub = @{
    ApiBase    = 'https://api.github.com'
    ApiVersion = '2022-11-28'
    Owner      = $null
    Repo       = $null
}
$script:GitHubHeaders = $null
$script:AiReviewHeaderPattern = '^## AI review - (sonnet|opus)\b'
$script:GitHubCommentMaxLength = 65536

function Get-MainRepoRoot {
    <# Root of the primary checkout, even when invoked from inside a linked worktree. #>
    $common = git -C $PSScriptRoot rev-parse --path-format=absolute --git-common-dir
    if (-not $common) { throw 'Not inside a git repository.' }
    (Resolve-Path (Join-Path $common '..')).Path
}

function Initialize-GitHubRepo {
    <# Fills Owner/Repo from the origin remote once. Accepts https and ssh remotes. #>
    if ($script:GitHub.Owner) { return }
    $remote = git -C (Get-MainRepoRoot) remote get-url origin
    if ($remote -notmatch 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/]+?)(\.git)?/?$') {
        throw "origin remote is not a GitHub URL: $remote"
    }
    $script:GitHub.Owner = $Matches.owner
    $script:GitHub.Repo  = $Matches.repo
}

function Get-GitHubRepoPath {
    <# '/repos/<owner>/<repo>' plus $Path (starts with '/' or is empty). #>
    param([string]$Path = '')
    Initialize-GitHubRepo
    "/repos/$($script:GitHub.Owner)/$($script:GitHub.Repo)$Path"
}

function Get-GitHubHeaders {
    <# Returns a copy of the cached auth headers. Token comes from the git credential helper. #>
    if ($script:GitHubHeaders) { return $script:GitHubHeaders.Clone() }

    # interactive=never: a cache miss must fail fast, not open the credential manager GUI.
    $cred  = "protocol=https`nhost=github.com`n`n" | git -c credential.interactive=never credential fill 2>$null
    $token = ($cred | Where-Object { $_ -like 'password=*' }) -replace '^password=', ''
    if (-not $token) { throw 'No GitHub credential: git credential helper returned no token for github.com. Push once over https to cache one.' }

    $h = @{
        Authorization          = "Bearer $token"
        Accept                 = 'application/vnd.github+json'
        'X-GitHub-Api-Version' = $script:GitHub.ApiVersion
        'User-Agent'           = 'yani-pr-review'
    }
    $probe = Invoke-WebRequest -Uri ($script:GitHub.ApiBase + (Get-GitHubRepoPath)) -Headers $h -UseBasicParsing -SkipHttpErrorCheck
    if ($probe.StatusCode -ne 200) { throw "GitHub REST rejected the git-cached token ($($probe.StatusCode)) for $(Get-GitHubRepoPath)." }
    $script:GitHubHeaders = $h
    $h.Clone()
}

function Invoke-GitHub {
    <#
    Authenticated REST call. $Uri may be a path ('/repos/...') or a full URL. $Body is converted
    to JSON (depth 10). JSON replies are parsed; empty replies (204) return $null. Non-2xx throws
    with the GitHub message and status code in the text.
    #>
    param(
        [Parameter(Mandatory)][string]$Uri,
        [ValidateSet('GET', 'POST', 'PATCH', 'PUT', 'DELETE')][string]$Method = 'GET',
        $Body
    )
    if ($Uri -notmatch '^https?://') { $Uri = $script:GitHub.ApiBase + $Uri }
    $p = @{ Uri = $Uri; Method = $Method; Headers = (Get-GitHubHeaders); UseBasicParsing = $true; SkipHttpErrorCheck = $true }
    if ($null -ne $Body) {
        $p.Body        = ConvertTo-Json -InputObject $Body -Depth 10 -Compress
        $p.ContentType = 'application/json'
    }
    $r = Invoke-WebRequest @p
    if ($r.StatusCode -ge 400) {
        $msg = try { ($r.Content | ConvertFrom-Json).message } catch { $r.Content }
        throw "GitHub $($r.StatusCode) for $Method $Uri : $msg"
    }
    if (-not $r.Content) { return $null }
    $r.Content | ConvertFrom-Json
}

function Get-GitHubPaged {
    <# GET every page of a list endpoint (per_page=100, follows until a short page). #>
    param([Parameter(Mandatory)][string]$Path)
    $sep  = if ($Path.Contains('?')) { '&' } else { '?' }
    $page = 1
    do {
        $chunk = @(Invoke-GitHub -Uri "$Path${sep}per_page=100&page=$page")
        $chunk
        $page++
    } while ($chunk.Count -eq 100)
}

function Get-AiReviewComments {
    <#
    Returns the PR's AI review comments (issue comments whose body starts with
    '## AI review - <model>'), oldest first. Each object gains a Model property.
    #>
    param([Parameter(Mandatory)][int]$PrNumber)
    $comments = @(Get-GitHubPaged -Path (Get-GitHubRepoPath -Path "/issues/$PrNumber/comments"))
    foreach ($c in ($comments | Sort-Object id)) {
        $first = ("$($c.body)" -split "`r?`n", 2)[0].Trim()
        if ($first -match $script:AiReviewHeaderPattern) {
            $c | Add-Member -NotePropertyName Model -NotePropertyValue $Matches[1] -Force
            $c
        }
    }
}

function Get-ReviewVerdict {
    <#
    Extracts approve|comment|needs-work from the review header (first 6 lines, so a verdict line
    quoted inside a finding cannot win). Throws when absent, unfilled, or present more than once.
    #>
    param([Parameter(Mandatory)][string]$Markdown)
    $header = (($Markdown -split "`r?`n") | Select-Object -First 6) -join "`n"
    # Anchored to end of line so the unfilled template "approve | comment | needs-work" fails.
    $m = [regex]::Matches($header, '(?m)^\*\*Verdict:\*\*\s*`?(approve|comment|needs-work)`?\s*$')
    if ($m.Count -ne 1) { throw "Review header (first 6 lines) must carry exactly one '**Verdict:** <approve|comment|needs-work>' line, found $($m.Count)." }
    $m[0].Groups[1].Value
}

function Get-RegisteredWorktrees {
    <# Absolute, backslash-normalised paths of every worktree git knows about for this repo. #>
    param([Parameter(Mandatory)][string]$RepoRoot)
    (git -C $RepoRoot worktree list --porcelain) -match '^worktree ' -replace '^worktree ', '' |
        ForEach-Object { $_ -replace '/', '\' }
}
