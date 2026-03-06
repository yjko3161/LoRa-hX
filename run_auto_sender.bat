@echo off
chcp 65001 >nul
title LoRa-hX 자동 송신기
echo LoRa-hX 자동 송신기를 시작합니다...
echo.
python auto_sender.py %*
if errorlevel 1 (
    echo.
    echo [오류] 송신기 실행 실패. 의존성을 확인하세요:
    echo   pip install -r requirements-server.txt
    echo.
)
pause
