@echo off
title Indian Railways AI Block Planning System - Unified Launcher
echo ======================================================================
echo   INDIAN RAILWAYS AI BLOCK PLANNING SYSTEM (PS-26027)
echo   Starting all services simultaneously...
echo ======================================================================
echo.

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py run_all.py
) else (
    python run_all.py
)

pause
