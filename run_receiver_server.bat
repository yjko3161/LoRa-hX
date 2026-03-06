@echo off
chcp 65001 >nul
title LoRa-hX 수신 서버
echo LoRa-hX 수신 서버를 시작합니다...
echo.
python receiver_server.py %*
if errorlevel 1 (
    echo.
    echo [오류] 서버 실행 실패. 의존성을 확인하세요:
    echo   pip install -r requirements-server.txt
    echo.
)
pause
