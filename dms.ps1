# Entry point for every command: .\dms.ps1 <command> [args]
# Runs `uv run dms <command>` with the repo-local environment (see scripts\dms-env.ps1).
# ASCII only (Windows PowerShell 5.1 reads BOM-less scripts in the ANSI code page).

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\dms-env.ps1')

$root = $PSScriptRoot
$uv = Get-DmsUv -Root $root
if (-not (Test-Path $uv)) {
    Write-Host 'uv is not installed in .tools\uv. Run .\bootstrap.ps1 first.' -ForegroundColor Red
    exit 1
}

$dmsArgs = $args
Invoke-DmsScope -Root $root -Body {
    & $uv run --locked --quiet --project $root dms @dmsArgs
}
exit $LASTEXITCODE
