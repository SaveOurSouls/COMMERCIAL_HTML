param(
    [switch]$NoBrowser,
    [switch]$SkipInstall,
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $projectRoot

if (Get-Command py -ErrorAction SilentlyContinue) {
    $bootstrapPython = "py"
    $bootstrapArgs = @("-3")
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $bootstrapPython = "python"
    $bootstrapArgs = @()
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $bootstrapPython = "python3"
    $bootstrapArgs = @()
}
else {
    throw "Python не найден. Установите Python 3.11+ и добавьте его в PATH."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $bootstrapPython @bootstrapArgs -m venv .venv
}

$venvPython = ".\.venv\Scripts\python.exe"

if (-not $SkipInstall) {
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -e ".[dev]"
}

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
}

if (-not $NoBrowser) {
    & "$PSScriptRoot\open_chrome.ps1" -Url "http://$BindHost`:$Port"
}

& $venvPython -m uvicorn app.main:app --host $BindHost --port $Port --reload
