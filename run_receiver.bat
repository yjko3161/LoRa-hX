@echo off
chcp 65001 >nul
echo ============================================================
echo   📥 USB-TO-LoRa-xF 수신기 (Receiver)
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
set /p PORT="수신기 COM 포트 입력 (예: COM4): "
if "%PORT%"=="" (
    echo [ERROR] 포트를 입력하세요.
    pause
    exit /b 1
)

:: 모드 선택
echo.
echo 수신 모드 선택:
echo   [1] 스트림 모드 (텍스트 수신, 기본)
echo   [2] 패킷 모드 (Hex 데이터 수신)
echo.
set /p MODE_CHOICE="선택 (1 또는 2, 기본=1): "
if "%MODE_CHOICE%"=="" set MODE_CHOICE=1

if "%MODE_CHOICE%"=="2" (
    set MODE=packet
) else (
    set MODE=stream
)

:: 로그 저장 여부
echo.
set /p SAVE_LOG="로그 파일 저장? (y/n, 기본=n): "
if /i "%SAVE_LOG%"=="y" (
    set LOG_OPT=--log received_%date:~0,4%%date:~5,2%%date:~8,2%.log
) else (
    set LOG_OPT=
)

:: 수신기 실행
echo.
echo ============================================================
echo   📥 수신기 시작: %PORT% / %MODE% 모드
echo   종료: Ctrl+C
echo ============================================================
echo.
python receiver.py --port %PORT% --mode %MODE% %LOG_OPT%

pause
