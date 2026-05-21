param(
    [switch]$NoBrowser,
    [switch]$SkipInstall,
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"

if (-not $SkipInstall) {
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
}

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
}

if (-not $NoBrowser) {
    & "$PSScriptRoot\open_chrome.ps1" -Url "http://$BindHost`:$Port"
}

python -m uvicorn app.main:app --host $BindHost --port $Port --reload
