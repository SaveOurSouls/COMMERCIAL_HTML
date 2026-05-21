@echo off
setlocal

set "ROOT=%~dp0..\.."
pushd "%ROOT%"

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install -e ".[dev]"
if errorlevel 1 goto :error

if not exist ".env" (
    if exist ".env.example" copy ".env.example" ".env" >nul
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0open_chrome.ps1" "http://127.0.0.1:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

popd
endlocal
exit /b 0

:error
echo Failed to start project on Windows 11.
popd
endlocal
exit /b 1
