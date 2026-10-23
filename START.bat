@echo off
setlocal
cd /d "%~dp0"
set "CODEARCH_PYTHON=python"
if exist ".runtime\python\fastapi" if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "CODEARCH_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist ".venv\Scripts\python.exe" set "CODEARCH_PYTHON=%~dp0.venv\Scripts\python.exe"
"%CODEARCH_PYTHON%" run.py %*
if errorlevel 1 pause
