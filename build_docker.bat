@echo off
setlocal

cd /d "%~dp0"

echo ==========================================
echo   RegulationManager - Docker Build
echo ==========================================
echo.

echo [1/2] Building Docker image (first time may take a few minutes)...
docker build -t regulation-manager-builder -f Dockerfile.linux .
if errorlevel 1 (
    echo Image build failed.
    pause
    exit /b 1
)
echo.

echo [2/2] Building Kylin x86_64...
docker run --rm -v "%cd%":/build regulation-manager-builder bash /build/build_docker.sh x86_64

echo.
echo ==========================================
echo   Done!
echo   Output: dist\RegulationManager_Kylin_x64\
echo ==========================================
pause
