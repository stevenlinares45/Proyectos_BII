@echo off
chcp 65001 >nul
cd /d "%~dp0"
python nuevo_proyecto.py
echo.
pause
