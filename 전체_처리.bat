@echo off
chcp 65001 >nul
echo === 1/2: 파일명 변경 ===
python "%~dp0rename_by_title.py"
echo.
echo === 2/2: 표 생성 ===
python "%~dp0generate_tables.py"
echo.
pause
