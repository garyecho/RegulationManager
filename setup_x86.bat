@echo off
chcp 437 >nul 2>&1
setlocal EnableDelayedExpansion

echo ==========================================
echo   Setup x86 (32-bit) Venv
echo ==========================================
echo.

cd /d "%~dp0"

REM [1/4] Check Python 3.8 32-bit
echo [1/4] Checking Python 3.8 32-bit ...
py -3.8-32 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo *** Python 3.8 32-bit NOT FOUND ***
    echo.
    echo You must install it first:
    echo   1. Go to: https://www.python.org/downloads/release/python-3810/
    echo   2. Download: "Windows x86 executable installer"
    echo   3. Install: DO NOT check "Add to PATH"
    echo   4. Re-run this script
    echo.
    pause
    exit /b 1
)
py -3.8-32 -c "import sys; print('Found: Python', sys.version)"
echo.

REM [2/4] Disable proxy
echo [2/4] Disabling proxy ...
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=
set NO_PROXY=*

REM [3/4] Create venv38_x86
echo [3/4] Creating venv38_x86 ...
if exist venv38_x86 (
    echo   venv38_x86 already exists, skipping.
) else (
    py -3.8-32 -m venv venv38_x86
    if errorlevel 1 (
        echo ERROR: Failed to create venv38_x86
        pause
        exit /b 1
    )
    echo   Created successfully.
)
echo.

REM [4/4] Install dependencies
echo [4/4] Installing dependencies ...
call venv38_x86\Scripts\activate.bat

REM Step A: Upgrade pip via HTTP mirror (avoids old-pip SSL/proxy bug)
echo   Upgrading pip ...
python -m pip install --upgrade pip -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

REM Step B: Install all deps
echo   Installing packages ...
pip install PyQt5==5.15.11 sqlalchemy whoosh jieba PyMuPDF==1.24.11 python-docx pyinstaller -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

if errorlevel 1 (
    echo.
    echo ERROR: pip install failed.
    echo.
    echo Possible fix: close VPN/proxy software, then re-run this script.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   DONE! venv38_x86 is ready.
echo   Next: build.bat
echo ==========================================
echo.
pause
