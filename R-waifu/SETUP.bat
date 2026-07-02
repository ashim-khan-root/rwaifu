@echo off
title R-waifu Setup
echo ===================================================
echo   R-waifu Setup
echo ===================================================
echo.

py -3 tools\setup_new_pc.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Setup failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Setup Complete!
echo   Run py -3 tools/read_context.py 10 to start
echo ===================================================
echo.
pause
