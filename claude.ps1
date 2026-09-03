<#
.SYNOPSIS
  Toggle Claude Code config home between global (~/.claude) and this repo (.claude-home).
.DESCRIPTION
  Run once  : sets CLAUDE_CONFIG_DIR to <repo>\.claude-home. Global work config, memory,
              plugins and hooks are NOT loaded. Only this repo's CLAUDE.md files apply.
  Run again : removes CLAUDE_CONFIG_DIR. Back to global ~/.claude.
  Always prints which home is active. Change persists for the current pwsh session.

  -Launch : force yani home on, then start claude (extra args pass through).
  -Status : print active home only, change nothing.
  -Off    : force global.
  -On     : force yani.

  First launch with yani home requires login once; credentials stored in .claude-home\ (gitignored).
#>
[CmdletBinding()]
param(
    [switch] $Launch,
    [switch] $Status,
    [switch] $On,
    [switch] $Off,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ClaudeArgs
)

$repo   = $PSScriptRoot
$yani   = Join-Path $repo '.claude-home'
$global = Join-Path $HOME '.claude'

function Show-Home {
    $cur = $env:CLAUDE_CONFIG_DIR
    if ($cur -and ($cur -ieq $yani)) {
        Write-Host 'CLAUDE HOME : yani (isolated)' -ForegroundColor Green
        Write-Host "  path      : $yani"
        Write-Host '  loads     : this repo CLAUDE.md + .claude\settings.json only'
    }
    elseif ($cur) {
        Write-Host 'CLAUDE HOME : custom' -ForegroundColor Yellow
        Write-Host "  path      : $cur"
    }
    else {
        Write-Host 'CLAUDE HOME : global (work)' -ForegroundColor Cyan
        Write-Host "  path      : $global"
        Write-Host '  loads     : global CLAUDE.md, memory, plugins, hooks + this repo CLAUDE.md'
    }
}

if ($Status) { Show-Home; return }

$isYani = $env:CLAUDE_CONFIG_DIR -and ($env:CLAUDE_CONFIG_DIR -ieq $yani)

if ($Off) { $target = 'global' }
elseif ($On -or $Launch) { $target = 'yani' }
else { $target = if ($isYani) { 'global' } else { 'yani' } }

if ($target -eq 'yani') {
    New-Item -ItemType Directory -Force -Path $yani | Out-Null
    $env:CLAUDE_CONFIG_DIR = $yani
}
else {
    Remove-Item Env:\CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
}

Show-Home

if ($Launch) {
    Set-Location $repo
    & claude @ClaudeArgs
}