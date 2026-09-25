@echo off
REM Script to install all optional dependencies (dlib and pyaudio)
echo ============================================
echo Installing Optional Dependencies
echo ============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Not running as administrator
    echo Some installations may require administrator privileges
    echo.
)

REM Setup Visual Studio environment
set "VS_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
if exist "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" (
    echo Setting up Visual Studio environment...
    call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat"
    echo Environment setup complete.
    echo.
)

REM Install dlib
echo ============================================
echo Step 1: Installing dlib
echo ============================================
py -3.11 -m pip install dlib
if %ERRORLEVEL% EQU 0 (
    echo [OK] dlib installed successfully
) else (
    echo [FAILED] dlib installation failed
    echo This is optional - Face AI can work without dlib
)
echo.

REM Install pyaudio
echo ============================================
echo Step 2: Installing pyaudio
echo ============================================
py -3.11 -m pip install pyaudio
if %ERRORLEVEL% EQU 0 (
    echo [OK] pyaudio installed successfully
) else (
    echo [FAILED] pyaudio installation failed
    echo This is optional - Voice Detection can work without pyaudio
    echo.
    echo You can download wheel file from:
    echo https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo For Python 3.11: PyAudio-0.2.14-cp311-cp311-win_amd64.whl
)
echo.

echo ============================================
echo Installation Summary
echo ============================================
echo Check the messages above for installation status.
echo.

pause

