@echo off
REM Script to install pyaudio
echo ============================================
echo Installing pyaudio
echo ============================================

echo.
echo Method 1: Trying to install from PyPI...
py -3.11 -m pip install pyaudio

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo pyaudio installed successfully!
    echo ============================================
    pause
    exit /b 0
)

echo.
echo Method 1 failed. Trying Method 2: Using wheel file...
echo.
echo Please download PyAudio wheel file from:
echo https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
echo.
echo For Python 3.11, download: PyAudio-0.2.14-cp311-cp311-win_amd64.whl
echo.
echo Then run:
echo py -3.11 -m pip install PyAudio-0.2.14-cp311-cp311-win_amd64.whl
echo.

pause

