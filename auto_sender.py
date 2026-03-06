"""
자동 송신기 — 센서 장비 → LoRa 중계
센서 시리얼 데이터를 읽어 LoRa 모듈로 전송
"""

import sys
import os
import argparse
import signal
import time

import serial

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from server.config import load_config


class AutoSender:
    """센서 → LoRa 자동 중계기"""

    def __init__(self, sensor_port: str, sensor_baud: int,
                 lora_port: str, lora_baud: int, interval: float = 1.0):
        self.sensor_port = sensor_port
        self.sensor_baud = sensor_baud
        self.lora_port = lora_port
        self.lora_baud = lora_baud
        self.interval = interval
        self.sensor_ser = None
        self.lora_ser = None
        self.running = False
        self.tx_count = 0

    def connect(self) -> bool:
        """센서 + LoRa 시리얼 포트 연결"""
        try:
            self.sensor_ser = serial.Serial(
                port=self.sensor_port,
                baudrate=self.sensor_baud,
                timeout=1.0,
            )
            print(f"[SENSOR] 연결: {self.sensor_port} @ {self.sensor_baud}")
        except serial.SerialException as e:
            print(f"[ERROR] 센서 포트 열기 실패: {e}")
            return False

        try:
            self.lora_ser = serial.Serial(
                port=self.lora_port,
                baudrate=self.lora_baud,
                timeout=1.0,
            )
            print(f"[LORA TX] 연결: {self.lora_port} @ {self.lora_baud}")
        except serial.SerialException as e:
            print(f"[ERROR] LoRa 포트 열기 실패: {e}")
            self.sensor_ser.close()
            return False

        return True

    def disconnect(self):
        """포트 닫기"""
        if self.sensor_ser and self.sensor_ser.is_open:
            self.sensor_ser.close()
        if self.lora_ser and self.lora_ser.is_open:
            self.lora_ser.close()
        print(f"[INFO] 송신기 종료 (총 {self.tx_count}건 전송)")

    def run(self):
        """메인 중계 루프"""
        self.running = True
        print("=" * 60)
        print("  LoRa-hX 자동 송신기 (센서 → LoRa 중계)")
        print(f"  센서: {self.sensor_port} → LoRa: {self.lora_port}")
        print(f"  중계 간격: {self.interval}초")
        print("  Ctrl+C로 종료")
        print("=" * 60)
        print()

        while self.running:
            try:
                if self.sensor_ser.in_waiting > 0:
                    time.sleep(0.05)  # 데이터 완성 대기
                    data = self.sensor_ser.read(self.sensor_ser.in_waiting)

                    if data:
                        # LoRa로 중계
                        self.lora_ser.write(data)
                        self.lora_ser.flush()
                        self.tx_count += 1

                        timestamp = time.strftime("%H:%M:%S")
                        hex_str = " ".join(f"{b:02X}" for b in data)
                        text = data.decode("utf-8", errors="replace")
                        print(f"[{timestamp}] #{self.tx_count} ({len(data)}B)")
                        print(f"  TEXT: {text}")
                        print(f"  HEX:  {hex_str}")

                        time.sleep(self.interval)
                else:
                    time.sleep(0.01)

            except serial.SerialException as e:
                print(f"[ERROR] 시리얼 오류: {e}")
                time.sleep(2)

            except KeyboardInterrupt:
                break

    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="LoRa-hX 자동 송신기 (센서→LoRa 중계)")
    parser.add_argument("--config", "-c", default=None, help="config.yaml 경로")
    parser.add_argument("--sensor-port", default=None, help="센서 시리얼 포트")
    parser.add_argument("--sensor-baud", type=int, default=None, help="센서 시리얼 속도")
    parser.add_argument("--lora-port", default=None, help="LoRa 시리얼 포트")
    parser.add_argument("--lora-baud", type=int, default=None, help="LoRa 시리얼 속도")
    parser.add_argument("--interval", type=float, default=None, help="중계 간격 (초)")
    args = parser.parse_args()

    config = load_config(args.config)
    sc = config["auto_sender"]

    # CLI 오버라이드
    sensor_port = args.sensor_port or sc["sensor_port"]
    sensor_baud = args.sensor_baud or sc["sensor_baud"]
    lora_port = args.lora_port or sc["lora_port"]
    lora_baud = args.lora_baud or sc["lora_baud"]
    interval = args.interval if args.interval is not None else sc["interval"]

    sender = AutoSender(sensor_port, sensor_baud, lora_port, lora_baud, interval)

    if not sender.connect():
        sys.exit(1)

    def shutdown(sig=None, frame=None):
        sender.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        sender.run()
    finally:
        sender.disconnect()


if __name__ == "__main__":
    main()
