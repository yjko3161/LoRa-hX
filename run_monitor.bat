@echo off
chcp 65001 >nul
echo ============================================================
echo   📡📥 USB-TO-LoRa-xF 양방향 모니터
echo   (하나의 창에서 송신 + 수신 동시 처리)
echo ============================================================
echo.

:: 가상환경 확인
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] 가상환경이 없습니다. setup.bat를 먼저 실행하세요.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

:: COM 포트 자동 탐색 및 표시
echo 사용 가능한 COM 포트:
python -c "import serial.tools.list_ports; ports=list(serial.tools.list_ports.comports()); [print(f'  [{i+1}] {p.device} - {p.description}') for i,p in enumerate(ports)]; print() if ports else print('  (발견된 포트 없음)')"
echo.

:: 포트 입력
set /p PORT="COM 포트 입력 (예: COM3): "
if "%PORT%"=="" (
    echo [ERROR] 포트를 입력하세요.
    pause
    exit /b 1
)

:: 모니터 실행
python monitor.py --port %PORT%

pause
