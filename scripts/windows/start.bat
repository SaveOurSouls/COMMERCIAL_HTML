@echo off
setlocal

set "ROOT=%~dp0..\.."
pushd "%ROOT%"

set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=py -3"
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
    ) else (
        where python3 >nul 2>nul
        if not errorlevel 1 (
            set "PY_CMD=python3"
        )
    )
)

if "%PY_CMD%"=="" (
    echo Python not found. Install Python 3.11+ and add it to PATH.
    goto :error
)

if not exist ".venv\Scripts\python.exe" (
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

set "VENV_PY=.venv\Scripts\python.exe"

"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :error

"%VENV_PY%" -m pip install -e ".[dev]"
if errorlevel 1 goto :error

if not exist ".env" (
    if exist ".env.example" copy ".env.example" ".env" >nul
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0open_chrome.ps1" "http://127.0.0.1:8000"
"%VENV_PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

popd
endlocal
exit /b 0

:error
echo Failed to start project on Windows 11.
popd
endlocal
exit /b 1
