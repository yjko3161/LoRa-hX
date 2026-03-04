#!/bin/bash
echo "============================================================"
echo "  USB-TO-LoRa-xF 수신기 (Receiver)"
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
read -p "수신기 포트 입력 (예: /dev/ttyUSB0): " PORT
if [ -z "$PORT" ]; then
    echo "[ERROR] 포트를 입력하세요."
    exit 1
fi

# 모드 선택
echo
echo "수신 모드 선택:"
echo "  [1] 스트림 모드 (텍스트 수신, 기본)"
echo "  [2] 패킷 모드 (Hex 데이터 수신)"
echo
read -p "선택 (1 또는 2, 기본=1): " MODE_CHOICE
MODE_CHOICE="${MODE_CHOICE:-1}"

if [ "$MODE_CHOICE" = "2" ]; then
    MODE="packet"
else
    MODE="stream"
fi

# 로그 저장 여부
echo
read -p "로그 파일 저장? (y/n, 기본=n): " SAVE_LOG
SAVE_LOG="${SAVE_LOG:-n}"

if [ "${SAVE_LOG,,}" = "y" ]; then
    LOG_OPT="--log received_$(date +%Y%m%d).log"
else
    LOG_OPT=""
fi

# 수신기 실행
echo
echo "============================================================"
echo "  수신기 시작: $PORT / $MODE 모드"
echo "  종료: Ctrl+C"
echo "============================================================"
echo
python3 receiver.py --port "$PORT" --mode "$MODE" $LOG_OPT
