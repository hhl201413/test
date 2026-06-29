@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" 签到.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" 签到.py
) else (
    python 签到.py
)
