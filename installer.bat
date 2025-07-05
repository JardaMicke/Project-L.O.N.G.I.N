@echo off
setlocal
title L.O.N.G.I.N. System Installer

echo.
echo =================================================
echo =      L.O.N.G.I.N. System Installer for Windows      =
echo =================================================
echo.

REM --- 1. Check for Prerequisites ---
echo [1/5] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in your PATH.
    echo Please install Python 3.8+ and ensure it's added to your PATH.
    goto :error
)
echo      - Python found.

echo.
echo [2/5] Checking for Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not found in your PATH.
    echo Please install Git and ensure it's added to your PATH.
    goto :error
)
echo      - Git found.
echo.

REM --- 2. Set up Virtual Environment ---
set VENV_DIR=.venv
echo [3/5] Setting up Python virtual environment in '%VENV_DIR%'...
if not exist "%VENV_DIR%" (
    echo      - Creating new virtual environment...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        goto :error
    )
) else (
    echo      - Virtual environment already exists. Skipping creation.
)
echo.

REM --- 3. Install Dependencies ---
echo [4/5] Activating virtual environment and installing dependencies...
call "%VENV_DIR%\Scripts\activate.bat"

echo      - Installing packages from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies from requirements.txt.
    goto :error
)

echo      - Installing the L.O.N.G.I.N. project in editable mode...
pip install -e .
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install the project.
    goto :error
)
echo.

REM --- 4. Create Helper Scripts ---
echo [5/5] Creating helper scripts (start_longin.bat and uninstall.bat)...

REM Create start_longin.bat
(
    echo @echo off
    echo title L.O.N.G.I.N. System
    echo echo Activating virtual environment...
    echo call "%~dp0.venv\Scripts\activate.bat"
    echo echo Starting L.O.N.G.I.N. API server on http://localhost:8000
    echo echo (Press CTRL+C to stop the server)
    echo uvicorn src.api:app --host 0.0.0.0 --port 8000
    echo pause
) > start_longin.bat

REM Create uninstall.bat
(
    echo @echo off
    echo title L.O.N.G.I.N. Uninstaller
    echo echo This will remove the Python virtual environment and helper scripts.
    echo set /p "confirm=Are you sure you want to uninstall? (y/n): "
    echo if /i "%%confirm%%" neq "y" (
    echo     echo Uninstall cancelled.
    echo     goto :eof
    echo )
    echo.
    echo echo Deleting virtual environment (.venv)...
    echo rmdir /s /q .venv
    echo.
    echo echo Deleting helper scripts...
    echo del start_longin.bat
    echo del uninstall.bat
    echo.
    echo echo Uninstall complete. You may now delete this script.
    echo pause
) > uninstall.bat

echo      - Helper scripts created successfully.
echo.

REM --- 5. Finish ---
echo =================================================
echo =           Installation Successful!            =
echo =================================================
echo.
echo To start the application, run the 'start_longin.bat' script.
echo.
goto :end

:error
echo.
echo =================================================
echo =             Installation Failed!              =
echo =================================================
echo.
echo Please check the error messages above and try again.

:end
pause
endlocal
