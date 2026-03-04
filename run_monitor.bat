@echo off
chcp 65001 >nul
echo ============================================================
echo   USB-TO-LoRa-xF 양방향 모니터
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
val = input('포트 입력 (번호 또는 이름, 예: 1 또는 COM30): ').strip()
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

:: 모니터 실행
echo.
echo ============================================================
echo   모니터 시작: %PORT%
echo   종료: quit 입력 또는 Ctrl+C
echo ============================================================
echo.
python monitor.py --port %PORT%

pause
