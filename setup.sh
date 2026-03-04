#!/bin/bash
echo "============================================================"
echo "  USB-TO-LoRa-xF 가상환경 설정"
echo "============================================================"
echo

# sudo로 실행 방지 (venv 소유권 문제)
if [ "$EUID" -eq 0 ]; then
    echo "[ERROR] sudo 없이 실행하세요: bash setup.sh"
    exit 1
fi

# 스크립트 위치로 이동
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 가상환경 생성
if [ ! -d "venv" ]; then
    echo "[1/3] 가상환경 생성 중..."
    python3 -m venv venv
    echo "      완료!"
else
    echo "[1/3] 가상환경이 이미 존재합니다."
fi

# 가상환경 활성화 및 패키지 설치
echo "[2/3] 패키지 설치 중..."
source venv/bin/activate
pip install pyserial --quiet

echo "[3/3] 설치 확인 중..."
python3 -c "import serial; print(f'      pyserial {serial.VERSION} 설치됨')"

# 실행 권한 부여
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null

# dialout 그룹 확인 (시리얼 포트 권한)
echo
if groups "$USER" 2>/dev/null | grep -qE 'dialout|tty|uucp'; then
    echo "[INFO] 시리얼 포트 권한 이미 있음"
else
    echo "[INFO] 시리얼 포트 권한 설정 중..."
    sudo usermod -a -G dialout "$USER" 2>/dev/null || \
    sudo usermod -a -G tty "$USER" 2>/dev/null || \
    echo "[WARN] 권한 설정 실패 시 수동으로: sudo chmod 666 /dev/ttyUSB0"
    echo "[INFO] 재로그인 후 적용됩니다"
fi

echo
echo "============================================================"
echo "  설정 완료! 아래 명령으로 실행하세요:"
echo
echo "  bash run_gui.sh       - GUI 통합 도구 (추천!)"
echo "  bash run_receiver.sh  - 수신기 실행"
echo "  bash run_sender.sh    - 송신기 실행"
echo "  bash run_monitor.sh   - 양방향 모니터"
echo "============================================================"
