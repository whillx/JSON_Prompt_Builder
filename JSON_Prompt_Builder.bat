@echo off
rem Launcher for Windows. Uses uv when available so the app runs on a
rem uv-managed Python; otherwise falls back to the system python.
cd /d "%~dp0"

where uv >nul 2>nul
if %errorlevel%==0 (
    uv run main.py
) else (
    python main.py
)

rem Keep the window open on errors so the message can be read.
if errorlevel 1 pause
