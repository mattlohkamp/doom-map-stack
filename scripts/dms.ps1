# Entry point for every command: .\scripts\dms.ps1 <command> [args]
# Runs `uv run dms <command>` with the repo-local environment (see dms-env.ps1).
# If anything is missing (a fresh clone), it runs bootstrap.ps1 first, so every launcher installs
# what it needs by itself.
# ASCII only (Windows PowerShell 5.1 reads BOM-less scripts in the ANSI code page).

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'dms-env.ps1')

$root = Get-DmsRoot
$uv = Get-DmsUv -Root $root
$project = Get-DmsProject -Root $root
$dmsArgs = $args

if (-not (Test-DmsInstalled -Root $root)) {
    # Claude Code's hooks run this too: they stay quiet and leave the install to a real command.
    if ($dmsArgs.Count -gt 0 -and $dmsArgs[0] -eq 'agent-hook') { exit 0 }
    Write-Host 'First run in this folder: installing what is missing into .tools\ (a few minutes).' -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'bootstrap.ps1')
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host ''
}

Invoke-DmsScope -Root $root -Body {
    & $uv run --locked --quiet --project $project dms @dmsArgs
}
exit $LASTEXITCODE
