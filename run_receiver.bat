@echo off
chcp 65001 >nul
echo ============================================================
echo   USB-TO-LoRa-xF 수신기 (Receiver)
echo ============================================================
echo.

:: 가상환경 확인
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] 가상환경이 없습니다. setup.bat를 먼저 실행하세요.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

:: Python으로 포트 선택 후 결과를 임시파일에 저장
python -c "
import serial.tools.list_ports, sys

ports = list(serial.tools.list_ports.comports())
if not ports:
    print('  (발견된 포트 없음)')
else:
    print('사용 가능한 COM 포트:')
    for i, p in enumerate(ports):
        print(f'  [{i+1}] {p.device} - {p.description}')

print()
val = input('수신기 포트 입력 (번호 또는 이름, 예: 1 또는 COM30): ').strip()
if not val:
    print('ERROR')
    sys.exit(1)

if val.isdigit():
    idx = int(val) - 1
    if 0 <= idx < len(ports):
        port = ports[idx].device
    else:
        print('ERROR')
        sys.exit(1)
else:
    port = val

with open('_port_sel.tmp', 'w') as f:
    f.write(port)
print(f'  -> {port} 선택됨')
"
if errorlevel 1 (
    echo [ERROR] 포트 선택 실패
    pause
    exit /b 1
)

:: 선택된 포트 읽기
set /p PORT=<_port_sel.tmp
del _port_sel.tmp >nul 2>&1

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
echo   수신기 시작: %PORT% / %MODE% 모드
echo   종료: Ctrl+C
echo ============================================================
echo.
python receiver.py --port %PORT% --mode %MODE% %LOG_OPT%

pause
