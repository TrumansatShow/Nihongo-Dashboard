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
echo  [1/4] Installing build dependencies (PyInstaller, pystray, Pillow)...
%PY% -m pip install --upgrade pyinstaller pystray Pillow
if %errorlevel% neq 0 (
    echo  ERROR: Dependency install failed.
    pause
    exit
)

echo.
echo  [2/4] Cleaning previous build...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist "Nihongo Dashboard.spec" del "Nihongo Dashboard.spec"

echo.
echo  [3/4] Building executable (no console window)...
%PY% -m PyInstaller --onefile --noconsole --name "Nihongo Dashboard" --add-data "dashboard.html;." --clean server.py
if %errorlevel% neq 0 (
    echo  ERROR: Build failed.
    pause
    exit
)

echo.
echo  [4/4] Copying dashboard.html to dist folder...
copy dashboard.html "dist\dashboard.html" >nul

echo.
echo  ========================================
echo   Done!  Built: dist\Nihongo Dashboard.exe
echo  ========================================
echo.
echo  How it works:
echo   - Double-click the exe
echo   - It runs hidden in your system tray (look for a red 日 icon)
echo   - Click the icon to open the dashboard
echo   - Right-click for menu: Start with Windows / Quit
echo   - No console window!
echo.
pause
