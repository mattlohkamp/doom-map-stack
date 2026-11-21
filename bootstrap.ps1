# One-time setup on a fresh clone; safe to re-run (only fills in what's missing).
#   1. Fetch the pinned standalone uv.exe into .tools\uv\ and check its hash.
#   2. Install the pinned Python into .tools\python\ (no registry entries, no shortcuts).
#   3. uv sync: dependencies into .venv\.
#   4. dms setup: engine, editor and IWAD into .tools\.
# ASCII only (Windows PowerShell 5.1 reads BOM-less scripts in the ANSI code page).

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest is very slow with the progress bar on 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

. (Join-Path $PSScriptRoot 'scripts\dms-env.ps1')
$root = $PSScriptRoot

# The uv version is pinned once, in uv.toml (required-version = "==X.Y.Z").
# The hash below is for that version's uv-x86_64-pc-windows-msvc.zip; update both together.
$uvSha256 = 'edd61f7f5728a56cc62455386661860bdfc7bab65872f39b0c25bdcc1d8e1beb'

$uvToml = Get-Content (Join-Path $root 'uv.toml') -Raw
if ($uvToml -notmatch '(?m)^required-version\s*=\s*"==([0-9.]+)"') {
    throw 'uv.toml must pin uv exactly: required-version = "==X.Y.Z"'
}
$uvVersion = $Matches[1]

function Write-Step([string]$text) { Write-Host "==> $text" -ForegroundColor Cyan }

# --- 1. uv ---------------------------------------------------------------
$uv = Get-DmsUv -Root $root
$uvDir = Split-Path $uv
$haveUv = $false
if (Test-Path $uv) {
    $current = (& $uv --version) -replace '^uv (\S+).*$', '$1'
    $haveUv = ($current -eq $uvVersion)
}
if ($haveUv) {
    Write-Step "uv $uvVersion already installed"
}
else {
    Write-Step "Fetching uv $uvVersion"
    $downloads = Join-Path $root '.tools\downloads'
    New-Item -ItemType Directory -Force $downloads | Out-Null
    $zip = Join-Path $downloads "uv-$uvVersion-x86_64-pc-windows-msvc.zip"
    $url = "https://github.com/astral-sh/uv/releases/download/$uvVersion/uv-x86_64-pc-windows-msvc.zip"
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $uvSha256) {
        Remove-Item $zip
        throw "uv download hash mismatch: expected $uvSha256, got $hash"
    }
    $staging = Join-Path $downloads "uv-$uvVersion"
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
    Expand-Archive $zip -DestinationPath $staging
    New-Item -ItemType Directory -Force $uvDir | Out-Null
    Copy-Item (Join-Path $staging 'uv.exe') $uv -Force
    Remove-Item $staging -Recurse -Force
    Write-Host "    $uv"
}

$failed = $false
Push-Location $root   # uv python install reads .python-version from the current directory
try {
Invoke-DmsScope -Root $root -Body {
    # --- 2. Python (version from .python-version) --------------------------
    Write-Step 'Installing Python into .tools\python'
    & $uv python install --no-registry --no-bin
    if ($LASTEXITCODE -ne 0) { $script:failed = $true; return }

    # --- 3. Dependencies ---------------------------------------------------
    Write-Step 'uv sync'
    & $uv sync --locked --project $root
    if ($LASTEXITCODE -ne 0) { $script:failed = $true; return }

    # --- 4. Doom tools -----------------------------------------------------
    Write-Step 'dms setup'
    & $uv run --locked --quiet --project $root dms setup
    if ($LASTEXITCODE -ne 0) { $script:failed = $true; return }
}
}
finally { Pop-Location }
if ($failed) {
    Write-Host 'bootstrap failed (see above).' -ForegroundColor Red
    exit 1
}
Write-Step 'Done. Run commands as .\dms.ps1 <command>.'
