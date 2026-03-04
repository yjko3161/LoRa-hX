"""
USB-TO-LoRa-xF 진단 스크립트
현재 모듈 상태 및 설정 확인

사용법:
    python3 diagnose.py --port /dev/ttyUSB0
    python diagnose.py --port COM3
"""

import serial
import time
import argparse
import sys


def send_raw(ser, cmd, wait=0.5):
    ser.write(cmd if isinstance(cmd, bytes) else (cmd + '\r\n').encode())
    ser.flush()
    time.sleep(wait)
    resp = b''
    while ser.in_waiting:
        resp += ser.read(ser.in_waiting)
        time.sleep(0.05)
    return resp.decode('utf-8', errors='replace').strip()


def main():
    parser = argparse.ArgumentParser(description="LoRa 모듈 진단")
    parser.add_argument('--port', '-p', required=True, help='시리얼 포트')
    parser.add_argument('--baud', '-b', type=int, default=115200)
    args = parser.parse_args()

    print("=" * 60)
    print("  USB-TO-LoRa-xF 진단 도구")
    print("=" * 60)

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
        print(f"[OK] 포트 열림: {args.port} @ {args.baud}")
    except Exception as e:
        print(f"[FAIL] 포트 열기 실패: {e}")
        sys.exit(1)

    time.sleep(0.3)

    # 1) 혹시 데이터 모드에서 수신되는 게 있는지 확인
    print("\n[1/4] 데이터 모드 수신 확인 (1초 대기)...")
    time.sleep(1.0)
    if ser.in_waiting:
        raw = ser.read(ser.in_waiting)
        print(f"  → 데이터 있음: {raw.hex().upper()} ({len(raw)}B) = {raw!r}")
    else:
        print("  → 수신 데이터 없음 (정상 또는 신호 없음)")

    # 2) AT 모드 진입 시도
    print("\n[2/4] AT 모드 진입 시도 (+++)")
    ser.reset_input_buffer()
    resp = send_raw(ser, b'+++\r\n', wait=0.8)
    if resp:
        print(f"  → 응답: {resp!r}")
        if 'OK' in resp or 'AT' in resp.upper():
            print("  → AT 모드 진입 성공")
        else:
            print("  → 응답 있음 (이미 AT 모드였을 수 있음)")
    else:
        print("  → 응답 없음 (이미 데이터 모드일 수 있음)")
        # 혹시 이미 AT 모드인지 테스트
        resp2 = send_raw(ser, 'AT', wait=0.5)
        if 'OK' in resp2:
            print("  → 이미 AT 모드 상태였음")
            resp = resp2

    # 3) 현재 설정 읽기
    print("\n[3/4] 현재 설정 읽기 (AT+AllP=?)")
    config_resp = send_raw(ser, 'AT+AllP=?', wait=1.0)
    if config_resp:
        print("  → 현재 설정:")
        for line in config_resp.splitlines():
            print(f"     {line}")
    else:
        print("  → 응답 없음 (AT 모드 진입 실패 가능)")

    # 버전 확인
    ver = send_raw(ser, 'AT+VER', wait=0.5)
    if ver:
        print(f"\n  → 펌웨어 버전: {ver}")

    # 4) AT 모드 종료 후 데이터 모드로 복귀
    print("\n[4/4] 데이터 모드 복귀 (AT+EXIT)")
    exit_resp = send_raw(ser, 'AT+EXIT', wait=0.5)
    print(f"  → 응답: {exit_resp!r}")

    ser.close()

    print()
    print("=" * 60)
    print("  진단 완료")
    print()
    print("  수신 안 될 경우 체크리스트:")
    print("  1) 송신/수신 장치의 SF, 채널, NetID 가 동일한지 확인")
    print("  2) 모듈이 데이터 모드인지 확인 (AT+EXIT 후 사용)")
    print("  3) 안테나 연결 확인")
    print("  4) 두 장치의 주파수 대역 일치 여부 확인")
    print("=" * 60)


if __name__ == '__main__':
    main()
