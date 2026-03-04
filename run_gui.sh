#!/bin/bash

# 가상환경 확인
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] 가상환경이 없습니다. 먼저 실행하세요: bash setup.sh"
    exit 1
fi
source venv/bin/activate

# GUI 실행
python3 lora_gui.py
