#!/bin/bash
echo "============================================================"
echo "  USB-TO-LoRa-xF 가상환경 설정"
echo "============================================================"
echo

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

# dialout 그룹 확인 (시리얼 포트 권한)
echo
if ! groups "$USER" | grep -q dialout; then
    echo "[INFO] 시리얼 포트 권한 설정 중..."
    sudo usermod -a -G dialout "$USER"
    echo "[INFO] dialout 그룹 추가 완료 (재로그인 후 적용됩니다)"
else
    echo "[INFO] dialout 그룹 권한 이미 있음"
fi

echo
echo "============================================================"
echo "  설정 완료! 아래 스크립트로 실행하세요:"
echo
echo "  ./run_gui.sh       - GUI 통합 도구 (추천!)"
echo "  ./run_receiver.sh  - 수신기 실행"
echo "  ./run_sender.sh    - 송신기 실행"
echo "  ./run_monitor.sh   - 양방향 모니터"
echo "============================================================"
