[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'down', 'logs', 'test', 'seed')]
    [string]$Command = 'up',
    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string[]]$Rest
)

$ErrorActionPreference = 'Stop'
$compose = Join-Path $PSScriptRoot 'compose.yaml'

switch ($Command) {
    'up'   { docker compose -f $compose up -d --build @Rest }
    'down' { docker compose -f $compose down @Rest }
    'logs' { docker compose -f $compose logs -f @Rest }
    'test' {
        Push-Location (Join-Path $PSScriptRoot 'ssot-api')
        try { uv run pytest @Rest } finally { Pop-Location }
    }
    'seed' { Write-Host 'No seeder yet.' }
}
