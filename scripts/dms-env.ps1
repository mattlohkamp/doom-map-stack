# Shared by bootstrap.ps1 and dms.ps1 (dot-sourced). ASCII only: Windows PowerShell 5.1
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

    # uv reads only the repo's uv.toml (a user-level %APPDATA%\uv\uv.toml is ignored).
    $env:UV_CONFIG_FILE = Join-Path $Root 'uv.toml'

    # Every uv location, as absolute paths (relative paths in uv.toml resolve against
    # the current directory, not the file, so they are set here instead).
    $env:UV_CACHE_DIR = Join-Path $tools 'uv-cache'
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $tools 'python'
    $env:UV_PYTHON_BIN_DIR = Join-Path $tools 'python-bin'
    $env:UV_TOOL_DIR = Join-Path $tools 'uv-tools'
    $env:UV_TOOL_BIN_DIR = Join-Path $tools 'uv-tools\bin'
    $env:UV_CREDENTIALS_DIR = Join-Path $tools 'uv-credentials'
    $env:UV_PROJECT_ENVIRONMENT = Join-Path $Root '.venv'

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
