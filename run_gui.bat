@echo off
chcp 65001 >nul

:: 가상환경 확인
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] 가상환경이 없습니다. setup.bat를 먼저 실행하세요.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

:: GUI 실행
start "" python lora_gui.py
