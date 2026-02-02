@echo off
REM Quick launcher for Windows
REM راه‌انداز سریع برای ویندوز

echo ==================================
echo 🚀 Fake Upload - Local Setup
echo ==================================
echo.

REM Default values
set GB=400
set THREADS=8
set PORT=8080

if not "%1"=="" set GB=%1
if not "%2"=="" set THREADS=%2

echo 📊 Configuration:
echo   - Upload: %GB% GB
echo   - Threads: %THREADS%
echo   - Port: %PORT%
echo.

echo 🔄 Starting server...
start "Fake Upload Server" python dummy_server.py -p %PORT%

timeout /t 3 /nobreak >nul

echo.
echo 🌐 Web interface: http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop
echo ==================================
echo.

REM Start upload
python fake_upload.py -g %GB% -p %PORT% -t %THREADS%

echo.
echo Upload finished!
pause
