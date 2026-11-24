# Shared by bootstrap.ps1 and dms.ps1 (dot-sourced; all three live in scripts\). ASCII only: Windows PowerShell 5.1
# reads BOM-less scripts in the ANSI code page.
#
# Invoke-DmsScope runs a script block with an environment that keeps uv and Python
# inside the repo, then restores the caller's environment, so the caller's shell is never changed.

function Set-DmsEnvironment {
    param([Parameter(Mandatory)][string]$Root)

    # Stop outside settings leaking in.
    $clear = @('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'VIRTUAL_ENV', 'CONDA_PREFIX')
    foreach ($name in $clear) { Remove-Item "Env:\$name" -ErrorAction SilentlyContinue }
    Get-ChildItem Env: | Where-Object { $_.Name -like 'PIP_*' -or $_.Name -like 'UV_*' } |
        ForEach-Object { Remove-Item "Env:\$($_.Name)" }

    $tools = Join-Path $Root '.tools'
    $env:DMS_ROOT = $Root

    # Temp files (uv's lock files, the editor's F9 test WAD) stay in the repo too.
    $tmp = Join-Path $tools 'tmp'
    New-Item -ItemType Directory -Force $tmp | Out-Null
    $env:TEMP = $tmp
    $env:TMP = $tmp

    # uv reads only the repo's src\uv.toml (a user-level %APPDATA%\uv\uv.toml is ignored).
    $env:UV_CONFIG_FILE = Join-Path $Root 'src\uv.toml'

    # Every uv location, as absolute paths (relative paths in uv.toml resolve against
    # the current directory, not the file, so they are set here instead).
    $env:UV_CACHE_DIR = Join-Path $tools 'uv-cache'
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $tools 'python'
    $env:UV_PYTHON_BIN_DIR = Join-Path $tools 'python-bin'
    $env:UV_TOOL_DIR = Join-Path $tools 'uv-tools'
    $env:UV_TOOL_BIN_DIR = Join-Path $tools 'uv-tools\bin'
    $env:UV_CREDENTIALS_DIR = Join-Path $tools 'uv-credentials'
    $env:UV_PROJECT_ENVIRONMENT = Join-Path $tools 'venv'

    # No registry entries, no python.exe shortcuts in the user profile.
    $env:UV_PYTHON_INSTALL_REGISTRY = '0'
    $env:UV_PYTHON_INSTALL_BIN = '0'
    $env:UV_PYTHON_NO_REGISTRY = '1'
}

function Invoke-DmsScope {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][scriptblock]$Body
    )
    $saved = @{}
    Get-ChildItem Env: | ForEach-Object { $saved[$_.Name] = $_.Value }
    try {
        Set-DmsEnvironment -Root $Root
        & $Body
    }
    finally {
        Get-ChildItem Env: | Where-Object { -not $saved.ContainsKey($_.Name) } |
            ForEach-Object { Remove-Item "Env:\$($_.Name)" }
        foreach ($k in $saved.Keys) { Set-Item "Env:\$k" $saved[$k] }
    }
}

function Get-DmsUv {
    param([Parameter(Mandatory)][string]$Root)
    return (Join-Path $Root '.tools\uv\uv.exe')
}

# The repo root: the folder above scripts\.
function Get-DmsRoot {
    return (Split-Path $PSScriptRoot -Parent)
}

# The Python project (pyproject.toml, uv.lock, uv.toml, .python-version): src\.
function Get-DmsProject {
    param([Parameter(Mandatory)][string]$Root)
    return (Join-Path $Root 'src')
}

# True once bootstrap.ps1 has run here: uv, the Python environment and the Doom tools are in .tools\.
function Test-DmsInstalled {
    param([Parameter(Mandatory)][string]$Root)
    foreach ($p in '.tools\uv\uv.exe', '.tools\venv\Scripts\python.exe', '.tools\tools.local.json') {
        if (-not (Test-Path (Join-Path $Root $p))) { return $false }
    }
    return $true
}
