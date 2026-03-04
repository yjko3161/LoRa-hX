#!/bin/bash
echo "============================================================"
echo "  USB-TO-LoRa-xF 양방향 모니터"
echo "  (하나의 창에서 송신 + 수신 동시 처리)"
echo "============================================================"
echo

# 가상환경 확인
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] 가상환경이 없습니다. 먼저 실행하세요: bash setup.sh"
    exit 1
fi
source venv/bin/activate

# 사용 가능한 시리얼 포트 표시
echo "사용 가능한 시리얼 포트:"
python3 -c "
import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
if ports:
    for i, p in enumerate(ports):
        print(f'  [{i+1}] {p.device} - {p.description}')
else:
    print('  (발견된 포트 없음)')
"
echo

# 포트 입력
read -p "포트 입력 (예: /dev/ttyUSB0): " PORT
if [ -z "$PORT" ]; then
    echo "[ERROR] 포트를 입력하세요."
    exit 1
fi

# 모니터 실행
python3 monitor.py --port "$PORT"
