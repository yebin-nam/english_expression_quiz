@echo off
chcp 65001 >nul
python "%~dp0generate_tables.py"
echo.
pause
