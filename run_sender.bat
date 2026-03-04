@echo off
chcp 65001 >nul
echo ============================================================
echo   📡 USB-TO-LoRa-xF 송신기 (Sender)
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
set /p PORT="송신기 COM 포트 입력 (예: COM3): "
if "%PORT%"=="" (
    echo [ERROR] 포트를 입력하세요.
    pause
    exit /b 1
)

:: 모드 선택
echo.
echo 전송 모드 선택:
echo   [1] 스트림 모드 - 대화형 (텍스트 입력하여 전송)
echo   [2] 패킷 모드 - 대화형 (주소/채널/Hex 지정 전송)
echo.
set /p MODE_CHOICE="선택 (1 또는 2, 기본=1): "
if "%MODE_CHOICE%"=="" set MODE_CHOICE=1

if "%MODE_CHOICE%"=="2" (
    set MODE=packet
) else (
    set MODE=stream
)

:: 송신기 실행 (대화형)
echo.
echo ============================================================
echo   📡 송신기 시작: %PORT% / %MODE% 모드 (대화형)
echo   종료: quit 또는 exit 입력
echo ============================================================
echo.
python sender.py --port %PORT% --mode %MODE% --interactive

pause
