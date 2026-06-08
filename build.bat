@echo off
chcp 437 >nul 2>&1
setlocal EnableDelayedExpansion

echo ==========================================
echo   RegulationManager - Build Script
echo   Usage: build.bat [x64 x86 all]
echo ==========================================
echo.

cd /d "%~dp0"

set BUILD_X64=0
set BUILD_X86=0

if "%1"=="" (
    set BUILD_X64=1
    set BUILD_X86=1
) else if /i "%1"=="x64" (
    set BUILD_X64=1
) else if /i "%1"=="x86" (
    set BUILD_X86=1
) else if /i "%1"=="all" (
    set BUILD_X64=1
    set BUILD_X86=1
) else (
    echo Unknown option: %1
    echo Usage: build.bat [x64 x86 all]
    pause
    exit /b 1
)

REM ==========================================
REM   64-bit Build
REM ==========================================

if !BUILD_X64!==1 (
    echo.
    echo ==========================================
    echo   Building 64-bit (x64)
    echo ==========================================

    if not exist "venv38\Scripts\activate.bat" (
        echo ERROR: venv38 not found.
        pause
        exit /b 1
    )

    call venv38\Scripts\activate.bat

    echo [x64] Cleaning ...
    if exist build rmdir /s /q build
    if exist dist\RegulationManager_x64 rmdir /s /q dist\RegulationManager_x64

    echo [x64] Building ...
    set BUILD_ARCH=x64
    pyinstaller RegulationManager.spec --clean --noconfirm
    if errorlevel 1 (
        echo [x64] BUILD FAILED
        pause
        exit /b 1
    )

    echo [x64] Preparing delivery ...
    mkdir "dist\RegulationManager_x64\data\documents" 2>nul
    mkdir "dist\RegulationManager_x64\data\backups" 2>nul
    mkdir "dist\RegulationManager_x64\data\logs" 2>nul
    copy /y "dist_files\README.txt" "dist\RegulationManager_x64\README.txt" >nul
    copy /y "dist_files\backup.txt" "dist\RegulationManager_x64\backup.txt" >nul
    echo [x64] DONE
)

REM ==========================================
REM   32-bit Build
REM ==========================================

if !BUILD_X86!==1 (
    echo.
    echo ==========================================
    echo   Building 32-bit (x86)
    echo ==========================================

    if not exist "venv38_x86\Scripts\activate.bat" (
        echo ERROR: venv38_x86 not found.
        echo Run setup_x86.bat first.
        pause
        exit /b 1
    )

    call venv38_x86\Scripts\activate.bat

    echo [x86] Cleaning ...
    if exist build rmdir /s /q build
    if exist dist\RegulationManager_x86 rmdir /s /q dist\RegulationManager_x86

    echo [x86] Building ...
    set BUILD_ARCH=x86
    pyinstaller RegulationManager.spec --clean --noconfirm
    if errorlevel 1 (
        echo [x86] BUILD FAILED
        pause
        exit /b 1
    )

    echo [x86] Preparing delivery ...
    mkdir "dist\RegulationManager_x86\data\documents" 2>nul
    mkdir "dist\RegulationManager_x86\data\backups" 2>nul
    mkdir "dist\RegulationManager_x86\data\logs" 2>nul
    copy /y "dist_files\README.txt" "dist\RegulationManager_x86\README.txt" >nul
    copy /y "dist_files\backup.txt" "dist\RegulationManager_x86\backup.txt" >nul
    echo [x86] DONE
)

echo.
echo ==========================================
echo   ALL BUILDS COMPLETE
echo ==========================================
if !BUILD_X64!==1 echo   x64: dist\RegulationManager_x64\
if !BUILD_X86!==1 echo   x86: dist\RegulationManager_x86\
echo ==========================================
echo.
pause
