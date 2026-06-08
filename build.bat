@echo off
echo ==========================================
echo   RegulationManager - Build Script
echo ==========================================
echo.

cd /d "%~dp0"

echo [0/4] Activating venv38 ...
if exist "venv38\Scripts\activate.bat" (
    call venv38\Scripts\activate.bat
) else (
    echo ERROR: venv38 not found
    pause
    exit /b 1
)

echo [1/4] Checking PyInstaller ...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller ...
    pip install pyinstaller
)

echo [2/4] Cleaning old builds ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/4] Building ...
pyinstaller RegulationManager.spec --clean --noconfirm
if errorlevel 1 (
    echo BUILD FAILED
    pause
    exit /b 1
)

echo [4/4] Preparing delivery ...

set DIST_DIR=dist\RegulationManager

if not exist "%DIST_DIR%" (
    echo ERROR: dist folder not found
    pause
    exit /b 1
)

mkdir "%DIST_DIR%\data\documents" 2>nul
mkdir "%DIST_DIR%\data\backups" 2>nul
mkdir "%DIST_DIR%\data\logs" 2>nul

copy /y "dist_files\README.txt" "%DIST_DIR%\README.txt" >nul
copy /y "dist_files\backup.txt" "%DIST_DIR%\backup.txt" >nul

echo.
echo ==========================================
echo   BUILD SUCCESS
echo   Output: %DIST_DIR%
echo   Exe:    %DIST_DIR%\RegulationManager.exe
echo ==========================================
echo.
echo NOTE: To rename exe to Chinese, run rename.bat
echo.
pause
