@echo off
setlocal
cd /d "%~dp0"
if exist ".runtime\python\fastapi" if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  echo This copy is already prepared. Run START.bat.
  pause
  exit /b 0
)
python scripts\bootstrap.py
if errorlevel 1 (
  echo Installation failed. Install Python 3.12 from python.org, add it to PATH, and try again.
  pause
  exit /b 1
)
pause
