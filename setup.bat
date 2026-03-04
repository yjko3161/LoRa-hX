@echo off
chcp 65001 >nul
echo ============================================================
echo   USB-TO-LoRa-xF 가상환경 설정
echo ============================================================
echo.

:: 가상환경 생성
if not exist "venv" (
    echo [1/3] 가상환경 생성 중...
    python -m venv venv
    echo       완료!
) else (
    echo [1/3] 가상환경이 이미 존재합니다.
)

:: 가상환경 활성화 및 패키지 설치
echo [2/3] 패키지 설치 중...
call venv\Scripts\activate.bat
pip install pyserial --quiet

echo [3/3] 설치 확인 중...
python -c "import serial; print(f'       pyserial {serial.VERSION} 설치됨')"

echo.
echo ============================================================
echo   설정 완료! 아래 배치파일로 실행하세요:
echo.
echo   run_gui.bat       - GUI 통합 도구 (추천!)
echo   run_receiver.bat  - 수신기 실행
echo   run_sender.bat    - 송신기 실행
echo   run_monitor.bat   - 양방향 모니터
echo ============================================================
pause
