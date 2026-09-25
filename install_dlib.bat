@echo off
REM Script to install dlib with Visual Studio Build Tools
echo ============================================
echo Installing dlib with Visual Studio Build Tools
echo ============================================

REM Find Visual Studio Build Tools
set "VS_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"

if not exist "%VS_PATH%" (
    echo ERROR: Visual Studio Build Tools not found at %VS_PATH%
    echo Please install Visual Studio Build Tools first.
    pause
    exit /b 1
)

echo Found Visual Studio Build Tools at %VS_PATH%

REM Setup environment
call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

REM Install dlib
echo.
echo Installing dlib...
py -3.11 -m pip install dlib

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo dlib installed successfully!
    echo ============================================
) else (
    echo.
    echo ============================================
    echo ERROR: Failed to install dlib
    echo ============================================
    echo Please check:
    echo 1. Visual Studio Build Tools is properly installed
    echo 2. C++ build tools workload is selected
    echo 3. Windows SDK is installed
    pause
    exit /b 1
)

pause

