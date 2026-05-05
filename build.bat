@echo off
title Building Nihongo Dashboard
echo.
echo  ========================================
echo   Nihongo Dashboard - Build Script
echo  ========================================
echo.

REM Find Python
where python >nul 2>&1
if %errorlevel%==0 (
    set PY=python
    goto found
)
where py >nul 2>&1
if %errorlevel%==0 (
    set PY=py
    goto found
)
echo  ERROR: Python not found.
echo  Install from https://www.python.org/downloads/
echo  Make sure to check "Add Python to PATH" during install.
pause
exit

:found
echo  [1/3] Installing PyInstaller...
%PY% -m pip install --upgrade pyinstaller
if %errorlevel% neq 0 (
    echo  ERROR: PyInstaller install failed.
    pause
    exit
)

echo.
echo  [2/3] Building executable...
%PY% -m PyInstaller --onefile --name "Nihongo Dashboard" --add-data "dashboard.html;." --icon=NONE --clean server.py
if %errorlevel% neq 0 (
    echo  ERROR: Build failed.
    pause
    exit
)

echo.
echo  [3/3] Copying dashboard.html to dist folder...
copy dashboard.html "dist\dashboard.html" >nul

echo.
echo  ========================================
echo   Done!  Built: dist\Nihongo Dashboard.exe
echo  ========================================
echo.
echo  Next steps:
echo   1. Zip the contents of dist\ together with README.md
echo   2. Upload as a GitHub Release
echo.
pause
