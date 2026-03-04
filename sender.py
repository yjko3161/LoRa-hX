"""
USB-TO-LoRa-xF 송신기 (Transmitter)
스트림 모드 및 패킷 모드 지원

사용법:
    python sender.py --port COM3 --mode stream --message "Hello LoRa!"
    python sender.py --port COM3 --mode packet --target-addr 65534 --target-ch 18 --message "Hello"
    python sender.py --port COM3 --mode stream --interactive
"""

import serial
import time
import argparse
import sys
from lora_config import LoRaConfig, LoRaParams


class LoRaSender:
    """USB-TO-LoRa-xF 데이터 송신 클래스"""

    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 1.0):
        self.config = LoRaConfig(port, baud_rate, timeout)
        self.ser = None

    def connect(self) -> bool:
        """장치 연결"""
        if self.config.open():
            self.ser = self.config.ser
            return True
        return False

    def disconnect(self):
        """장치 연결 해제"""
        self.config.close()

    def setup(self, params: LoRaParams) -> bool:
        """LoRa 매개변수 설정"""
        self.config.enter_at_mode()
        success = self.config.apply_params(params)
        self.config.exit_at_mode()
        time.sleep(0.5)  # 설정 적용 대기
        return success

    def send_stream(self, message: str) -> bool:
        """
        스트림 모드로 메시지 전송

        Args:
            message: 전송할 문자열 메시지
        Returns:
            전송 성공 여부
        """
        if not self.ser or not self.ser.is_open:
            print("[ERROR] 시리얼 포트가 열려있지 않습니다")
            return False

        try:
            data = message.encode('utf-8')
            self.ser.write(data)
            self.ser.flush()
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] 송신 (스트림): {message} ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"[ERROR] 전송 실패: {e}")
            return False

    def send_packet(self, target_addr: int, target_channel: int, data: bytes) -> bool:
        """
        패킷 모드로 데이터 전송
        패킷 형식: [주소(2바이트)] + [채널(1바이트)] + [데이터]

        Args:
            target_addr: 대상 장치 주소 (0~65535)
            target_channel: 대상 장치 채널 (0~80)
            data: 전송할 데이터 (bytes)
        Returns:
            전송 성공 여부
        """
        if not self.ser or not self.ser.is_open:
            print("[ERROR] 시리얼 포트가 열려있지 않습니다")
            return False

        try:
            # 주소: 2바이트 빅엔디안 + 채널: 1바이트 + 데이터
            addr_bytes = target_addr.to_bytes(2, byteorder='big')
            ch_byte = target_channel.to_bytes(1, byteorder='big')
            packet = addr_bytes + ch_byte + data

            self.ser.write(packet)
            self.ser.flush()

            timestamp = time.strftime('%H:%M:%S')
            hex_str = ' '.join(f'{b:02X}' for b in packet)
            print(f"[{timestamp}] 송신 (패킷): {hex_str}")
            print(f"  → 대상 주소: {target_addr} (0x{target_addr:04X})")
            print(f"  → 대상 채널: {target_channel} (0x{target_channel:02X})")
            print(f"  → 데이터: {data.hex().upper()} ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"[ERROR] 전송 실패: {e}")
            return False

    def send_broadcast(self, channel: int, data: bytes) -> bool:
        """
        브로드캐스트 전송 (패킷 모드, 주소=0xFFFF)

        Args:
            channel: 채널 번호
            data: 전송할 데이터
        """
        return self.send_packet(0xFFFF, channel, data)

    def interactive_stream(self):
        """스트림 모드 대화형 전송"""
        print("=" * 60)
        print("  USB-TO-LoRa-xF 대화형 송신기 (스트림 모드)")
        print("  'quit' 또는 'exit'를 입력하면 종료합니다")
        print("=" * 60)

        while True:
            try:
                message = input("\n📡 전송할 메시지: ").strip()
                if message.lower() in ('quit', 'exit', 'q'):
                    print("[INFO] 송신기를 종료합니다...")
                    break
                if not message:
                    continue
                self.send_stream(message)
            except KeyboardInterrupt:
                print("\n[INFO] 송신기를 종료합니다...")
                break

    def interactive_packet(self):
        """패킷 모드 대화형 전송"""
        print("=" * 60)
        print("  USB-TO-LoRa-xF 대화형 송신기 (패킷 모드)")
        print("  'quit' 또는 'exit'를 입력하면 종료합니다")
        print("=" * 60)

        while True:
            try:
                print()
                addr_str = input("  대상 주소 (0~65535, 65535=브로드캐스트): ").strip()
                if addr_str.lower() in ('quit', 'exit', 'q'):
                    break

                ch_str = input("  대상 채널 (0~80): ").strip()
                if ch_str.lower() in ('quit', 'exit', 'q'):
                    break

                data_str = input("  전송 데이터 (hex, 예: AABB): ").strip()
                if data_str.lower() in ('quit', 'exit', 'q'):
                    break

                target_addr = int(addr_str)
                target_ch = int(ch_str)
                data = bytes.fromhex(data_str)

                self.send_packet(target_addr, target_ch, data)

            except ValueError as e:
                print(f"[ERROR] 입력 오류: {e}")
            except KeyboardInterrupt:
                print("\n[INFO] 송신기를 종료합니다...")
                break


def main():
    parser = argparse.ArgumentParser(
        description="USB-TO-LoRa-xF 송신기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 스트림 모드로 단일 메시지 전송
  python sender.py --port COM3 --message "Hello LoRa!"

  # 스트림 모드 대화형 전송
  python sender.py --port COM3 --interactive

  # 패킷 모드로 특정 장치에 전송
  python sender.py --port COM3 --mode packet --target-addr 65534 --target-ch 18 --data AABBCC

  # 설정 변경 후 전송
  python sender.py --port COM3 --sf 9 --power 22 --channel 18 --message "Hi!"
        """,
    )

    # 기본 설정
    parser.add_argument('--port', '-p', required=True, help='시리얼 포트 (예: COM3)')
    parser.add_argument('--baud', '-b', type=int, default=115200, help='통신 속도 (기본: 115200)')
    parser.add_argument('--mode', '-m', choices=['stream', 'packet'], default='stream',
                        help='전송 모드 (기본: stream)')

    # 전송 데이터
    parser.add_argument('--message', '-M', help='전송할 메시지 (스트림 모드)')
    parser.add_argument('--data', '-d', help='전송할 Hex 데이터 (패킷 모드, 예: AABBCC)')
    parser.add_argument('--target-addr', type=int, default=65535, help='대상 주소 (패킷 모드, 기본: 65535)')
    parser.add_argument('--target-ch', type=int, default=18, help='대상 채널 (패킷 모드, 기본: 18)')
    parser.add_argument('--interactive', '-i', action='store_true', help='대화형 모드')
    parser.add_argument('--repeat', '-r', type=int, default=1, help='메시지 반복 전송 횟수')
    parser.add_argument('--interval', type=float, default=1.0, help='반복 전송 간격 (초)')

    # LoRa 매개변수 (선택적 설정 변경)
    parser.add_argument('--sf', type=int, help='확산 인자 (7~12)')
    parser.add_argument('--power', type=int, help='RF 출력 전력 (10~22 dBm)')
    parser.add_argument('--channel', type=int, help='송수신 채널 (0~80)')
    parser.add_argument('--address', type=int, help='장치 주소 (0~65535)')
    parser.add_argument('--net-id', type=int, help='네트워크 ID (0~65535)')
    parser.add_argument('--configure', '-c', action='store_true', help='매개변수 설정 적용')

    args = parser.parse_args()

    # 송신기 생성 및 연결
    sender = LoRaSender(args.port, args.baud)

    if not sender.connect():
        sys.exit(1)

    try:
        # 매개변수 설정 (요청 시)
        if args.configure or any([args.sf, args.power, args.channel, args.address, args.net_id]):
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
            sender.setup(params)

        # 대화형 모드
        if args.interactive:
            if args.mode == 'stream':
                sender.interactive_stream()
            else:
                sender.interactive_packet()
            return

        # 단일/반복 전송
        if args.mode == 'stream':
            if not args.message:
                print("[ERROR] 스트림 모드에서는 --message 옵션이 필요합니다")
                sys.exit(1)
            for i in range(args.repeat):
                sender.send_stream(args.message)
                if i < args.repeat - 1:
                    time.sleep(args.interval)

        elif args.mode == 'packet':
            if not args.data:
                print("[ERROR] 패킷 모드에서는 --data 옵션이 필요합니다")
                sys.exit(1)
            data = bytes.fromhex(args.data)
            for i in range(args.repeat):
                sender.send_packet(args.target_addr, args.target_ch, data)
                if i < args.repeat - 1:
                    time.sleep(args.interval)

    finally:
        sender.disconnect()


if __name__ == '__main__':
    main()
