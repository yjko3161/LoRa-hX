"""
USB-TO-LoRa-xF 수신기 (Receiver)
스트림 모드 및 패킷 모드 지원

사용법:
    python receiver.py --port COM4 --mode stream
    python receiver.py --port COM4 --mode packet
    python receiver.py --port COM4 --mode stream --log received.log
"""

import serial
import time
import argparse
import sys
import os
from datetime import datetime
from lora_config import LoRaConfig, LoRaParams


class LoRaReceiver:
    """USB-TO-LoRa-xF 데이터 수신 클래스"""

    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 0.5):
        self.config = LoRaConfig(port, baud_rate, timeout)
        self.ser = None
        self.log_file = None
        self.received_count = 0
        self.start_time = None

    def connect(self) -> bool:
        """장치 연결"""
        if self.config.open():
            self.ser = self.config.ser
            return True
        return False

    def disconnect(self):
        """장치 연결 해제"""
        if self.log_file:
            self.log_file.close()
        self.config.close()

    def setup(self, params: LoRaParams) -> bool:
        """LoRa 매개변수 설정"""
        self.config.enter_at_mode()
        success = self.config.apply_params(params)
        self.config.exit_at_mode()
        time.sleep(0.5)
        return success

    def enable_logging(self, log_path: str):
        """수신 데이터 로그 파일 저장 활성화"""
        self.log_file = open(log_path, 'a', encoding='utf-8')
        self.log_file.write(f"\n{'=' * 60}\n")
        self.log_file.write(f"수신 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.log_file.write(f"포트: {self.config.port}\n")
        self.log_file.write(f"{'=' * 60}\n")
        print(f"[INFO] 로그 파일: {os.path.abspath(log_path)}")

    def _log_data(self, timestamp: str, data_str: str, hex_str: str, size: int):
        """데이터 로그 기록"""
        if self.log_file:
            self.log_file.write(f"[{timestamp}] ({size}B) {data_str}")
            if hex_str:
                self.log_file.write(f" | HEX: {hex_str}")
            self.log_file.write("\n")
            self.log_file.flush()

    def receive_stream(self, callback=None):
        """
        스트림 모드 수신 (무한 루프)

        Args:
            callback: 수신 데이터 콜백 함수 (data: bytes, timestamp: str) -> None
        """
        if not self.ser or not self.ser.is_open:
            print("[ERROR] 시리얼 포트가 열려있지 않습니다")
            return

        self.start_time = time.time()
        print("=" * 60)
        print("  USB-TO-LoRa-xF 수신기 (스트림 모드)")
        print(f"  포트: {self.config.port} | 속도: {self.config.baud_rate}")
        print("  Ctrl+C를 누르면 종료합니다")
        print("=" * 60)
        print()

        try:
            while True:
                if self.ser.in_waiting > 0:
                    # 수신 버퍼에서 데이터 읽기
                    time.sleep(0.05)  # 패킷 완성 대기
                    data = self.ser.read(self.ser.in_waiting)

                    if data:
                        self.received_count += 1
                        timestamp = time.strftime('%H:%M:%S')
                        data_str = data.decode('utf-8', errors='replace')
                        hex_str = ' '.join(f'{b:02X}' for b in data)

                        print(f"📥 [{timestamp}] #{self.received_count}: {data_str}")
                        print(f"   HEX: {hex_str} ({len(data)} bytes)")

                        self._log_data(timestamp, data_str, hex_str, len(data))

                        if callback:
                            callback(data, timestamp)
                else:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            elapsed = time.time() - self.start_time
            print(f"\n\n[INFO] 수신기 종료")
            print(f"  총 수신: {self.received_count}건")
            print(f"  실행 시간: {elapsed:.1f}초")

    def receive_packet(self, callback=None):
        """
        패킷 모드 수신 (무한 루프)
        수신 데이터에서 소스 정보를 파싱

        Args:
            callback: 수신 데이터 콜백 함수
        """
        if not self.ser or not self.ser.is_open:
            print("[ERROR] 시리얼 포트가 열려있지 않습니다")
            return

        self.start_time = time.time()
        print("=" * 60)
        print("  USB-TO-LoRa-xF 수신기 (패킷 모드)")
        print(f"  포트: {self.config.port} | 속도: {self.config.baud_rate}")
        print("  Ctrl+C를 누르면 종료합니다")
        print("=" * 60)
        print()

        try:
            while True:
                if self.ser.in_waiting > 0:
                    time.sleep(0.05)
                    data = self.ser.read(self.ser.in_waiting)

                    if data:
                        self.received_count += 1
                        timestamp = time.strftime('%H:%M:%S')
                        hex_str = ' '.join(f'{b:02X}' for b in data)

                        print(f"📥 [{timestamp}] #{self.received_count}")
                        print(f"   RAW HEX: {hex_str} ({len(data)} bytes)")

                        # 패킷 데이터 파싱 (3바이트 이상이면 주소/채널 정보 포함)
                        if len(data) >= 3:
                            payload = data
                            payload_hex = ' '.join(f'{b:02X}' for b in payload)
                            print(f"   데이터: {payload_hex}")
                        else:
                            print(f"   데이터: {hex_str}")

                        self._log_data(timestamp, hex_str, "", len(data))

                        if callback:
                            callback(data, timestamp)
                else:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            elapsed = time.time() - self.start_time
            print(f"\n\n[INFO] 수신기 종료")
            print(f"  총 수신: {self.received_count}건")
            print(f"  실행 시간: {elapsed:.1f}초")

    def receive_once(self, timeout: float = 10.0) -> bytes:
        """
        단일 데이터 수신 (타임아웃까지 대기)

        Args:
            timeout: 대기 시간 (초)
        Returns:
            수신된 데이터 (bytes) 또는 빈 바이트
        """
        if not self.ser or not self.ser.is_open:
            return b""

        start = time.time()
        while time.time() - start < timeout:
            if self.ser.in_waiting > 0:
                time.sleep(0.05)
                data = self.ser.read(self.ser.in_waiting)
                if data:
                    return data
            time.sleep(0.01)
        return b""


def main():
    parser = argparse.ArgumentParser(
        description="USB-TO-LoRa-xF 수신기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 스트림 모드 수신
  python receiver.py --port COM4

  # 패킷 모드 수신
  python receiver.py --port COM4 --mode packet

  # 로그 파일과 함께 수신
  python receiver.py --port COM4 --log received.log

  # 설정 변경 후 수신
  python receiver.py --port COM4 --sf 9 --channel 18
        """,
    )

    parser.add_argument('--port', '-p', required=True, help='시리얼 포트 (예: COM4)')
    parser.add_argument('--baud', '-b', type=int, default=115200, help='통신 속도 (기본: 115200)')
    parser.add_argument('--mode', '-m', choices=['stream', 'packet'], default='stream',
                        help='수신 모드 (기본: stream)')
    parser.add_argument('--log', '-l', help='로그 파일 경로')

    # LoRa 매개변수
    parser.add_argument('--sf', type=int, help='확산 인자 (7~12)')
    parser.add_argument('--power', type=int, help='RF 출력 전력 (10~22 dBm)')
    parser.add_argument('--channel', type=int, help='송수신 채널 (0~80)')
    parser.add_argument('--address', type=int, help='장치 주소 (0~65535)')
    parser.add_argument('--net-id', type=int, help='네트워크 ID (0~65535)')
    parser.add_argument('--rssi', action='store_true', help='RSSI 출력 활성화')
    parser.add_argument('--configure', '-c', action='store_true', help='매개변수 설정 적용')

    args = parser.parse_args()

    # 수신기 생성 및 연결
    receiver = LoRaReceiver(args.port, args.baud)

    if not receiver.connect():
        sys.exit(1)

    try:
        # 매개변수 설정
        if args.configure or any([args.sf, args.power, args.channel, args.address, args.net_id, args.rssi]):
            params = LoRaParams()
            params.mode = 1 if args.mode == 'stream' else 2
            if args.sf:
                params.spreading_factor = args.sf
            if args.power:
                params.power = args.power
            if args.channel:
                params.tx_channel = args.channel
                params.rx_channel = args.channel
            if args.address:
                params.address = args.address
            if args.net_id:
                params.net_id = args.net_id
            if args.rssi:
                params.rssi = 1
            receiver.setup(params)

        # 로그 파일
        if args.log:
            receiver.enable_logging(args.log)

        # 수신 시작
        if args.mode == 'stream':
            receiver.receive_stream()
        else:
            receiver.receive_packet()

    finally:
        receiver.disconnect()


if __name__ == '__main__':
    main()
