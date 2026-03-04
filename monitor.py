"""
USB-TO-LoRa-xF 양방향 모니터 (송수신 동시)
하나의 장치에서 전송과 수신을 동시에 수행

수신인지 송신인지 구분:
  📡 TX → 내가 보낸 데이터 (송신)
  📥 RX ← 상대방이 보낸 데이터 (수신)

사용법:
    python monitor.py --port COM3
"""

import serial
import time
import threading
import sys
import argparse
from datetime import datetime
from lora_config import LoRaConfig, LoRaParams


class LoRaMonitor:
    """양방향 LoRa 모니터 - 송수신 구분 표시"""

    def __init__(self, port: str, baud_rate: int = 115200):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = False
        self.tx_count = 0
        self.rx_count = 0
        self.start_time = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,
            )
            return True
        except serial.SerialException as e:
            print(f"[ERROR] 포트 열기 실패: {e}")
            return False

    def disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _receive_loop(self):
        """수신 스레드 - 백그라운드에서 데이터 수신"""
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    time.sleep(0.05)
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        self.rx_count += 1
                        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        text = data.decode('utf-8', errors='replace')
                        hex_str = ' '.join(f'{b:02X}' for b in data)

                        # 수신 표시 - 파란색 화살표
                        print(f"\r  📥 RX ← [{ts}] #{self.rx_count}: {text}")
                        print(f"          HEX: {hex_str} ({len(data)}B)")
                        print(f"\n  📡 전송할 메시지: ", end="", flush=True)
                else:
                    time.sleep(0.01)
            except Exception:
                if self.running:
                    time.sleep(0.01)

    def run(self):
        """양방향 모니터 실행"""
        self.running = True
        self.start_time = time.time()

        print()
        print("╔══════════════════════════════════════════════════════════╗")
        print("║          USB-TO-LoRa-xF 양방향 모니터                  ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  포트: {self.port:<10}  속도: {self.baud_rate}                    ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║  📡 TX → 내가 보낸 데이터 (송신)                       ║")
        print("║  📥 RX ← 상대방이 보낸 데이터 (수신)                   ║")
        print("║                                                        ║")
        print("║  'quit' 입력 또는 Ctrl+C로 종료                        ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print()

        # 수신 스레드 시작
        rx_thread = threading.Thread(target=self._receive_loop, daemon=True)
        rx_thread.start()

        # 메인 루프 - 송신
        try:
            while self.running:
                message = input("  📡 전송할 메시지: ").strip()

                if message.lower() in ('quit', 'exit', 'q'):
                    break

                if not message:
                    continue

                # 전송
                try:
                    data = message.encode('utf-8')
                    self.ser.write(data)
                    self.ser.flush()
                    self.tx_count += 1
                    ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    hex_str = ' '.join(f'{b:02X}' for b in data)

                    # 송신 표시 - 빨간색 화살표
                    print(f"  📡 TX → [{ts}] #{self.tx_count}: {message}")
                    print(f"          HEX: {hex_str} ({len(data)}B)")
                    print()
                except Exception as e:
                    print(f"  [ERROR] 전송 실패: {e}")

        except KeyboardInterrupt:
            pass

        # 종료 통계
        self.running = False
        elapsed = time.time() - self.start_time
        print()
        print("┌──────────────────────────────────────────────────────────┐")
        print("│  📊 통신 통계                                           │")
        print(f"│  📡 TX (송신): {self.tx_count:>5}건                                │")
        print(f"│  📥 RX (수신): {self.rx_count:>5}건                                │")
        print(f"│  ⏱️  실행시간: {elapsed:>7.1f}초                               │")
        print("└──────────────────────────────────────────────────────────┘")


def main():
    parser = argparse.ArgumentParser(description="USB-TO-LoRa-xF 양방향 모니터")
    parser.add_argument('--port', '-p', required=True, help='COM 포트 (예: COM3)')
    parser.add_argument('--baud', '-b', type=int, default=115200, help='통신 속도')
    args = parser.parse_args()

    monitor = LoRaMonitor(args.port, args.baud)
    if monitor.connect():
        try:
            monitor.run()
        finally:
            monitor.disconnect()
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
