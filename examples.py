"""
USB-TO-LoRa-xF 사용 예제
기본적인 송수신 예제 및 설정 방법
"""

from lora_config import LoRaConfig, LoRaParams
from sender import LoRaSender
from receiver import LoRaReceiver
import time
import threading


# ============================================================
# 예제 1: 기본 스트림 모드 송신
# ============================================================
def example_stream_send():
    """스트림 모드로 메시지 전송"""
    sender = LoRaSender(port="COM3")  # ← 실제 포트로 변경

    if sender.connect():
        try:
            # 기본 설정으로 전송 (설정 변경 없이 바로 사용 가능)
            sender.send_stream("Hello LoRa!")
            time.sleep(1)
            sender.send_stream("안녕하세요 LoRa 테스트입니다")
        finally:
            sender.disconnect()


# ============================================================
# 예제 2: 기본 스트림 모드 수신
# ============================================================
def example_stream_receive():
    """스트림 모드로 메시지 수신"""
    receiver = LoRaReceiver(port="COM4")  # ← 실제 포트로 변경

    if receiver.connect():
        try:
            receiver.receive_stream()  # Ctrl+C로 종료
        finally:
            receiver.disconnect()


# ============================================================
# 예제 3: 매개변수 설정 후 송수신
# ============================================================
def example_with_config():
    """매개변수를 사용자 지정하여 통신"""
    params = LoRaParams(
        spreading_factor=9,      # SF9 (더 긴 거리, 느린 속도)
        bandwidth=0,             # 125KHz
        coding_rate=1,           # 4/5
        power=22,                # 최대 출력
        net_id=100,              # 네트워크 ID
        address=1,               # 장치 주소 1
        tx_channel=18,           # 채널 18
        rx_channel=18,
        mode=1,                  # 스트림 모드
        rssi=1,                  # RSSI 활성화
    )

    sender = LoRaSender(port="COM3")

    if sender.connect():
        try:
            sender.setup(params)  # AT 명령으로 설정 적용
            sender.send_stream("설정 변경 후 전송 테스트")
        finally:
            sender.disconnect()


# ============================================================
# 예제 4: 패킷 모드 송신
# ============================================================
def example_packet_send():
    """패킷 모드로 특정 장치에 데이터 전송"""
    sender = LoRaSender(port="COM3")

    if sender.connect():
        try:
            # 설정: 패킷 모드
            params = LoRaParams(mode=2)
            sender.setup(params)

            # 특정 장치 (주소: 0xFFFE=65534, 채널: 18)에 전송
            sender.send_packet(
                target_addr=65534,
                target_channel=18,
                data=bytes([0xAA, 0xBB, 0xCC]),
            )

            time.sleep(1)

            # 브로드캐스트 (주소: 0xFFFF)
            sender.send_broadcast(
                channel=18,
                data=bytes([0xDD, 0xEE]),
            )
        finally:
            sender.disconnect()


# ============================================================
# 예제 5: 수신 콜백 함수 사용
# ============================================================
def example_with_callback():
    """콜백 함수를 이용한 수신 데이터 처리"""

    def on_data_received(data: bytes, timestamp: str):
        """수신 데이터 처리 콜백"""
        text = data.decode('utf-8', errors='replace')
        print(f"  → 콜백 호출됨: {text}")
        # 여기에 원하는 처리 로직 추가
        # 예: 데이터베이스 저장, 센서 데이터 파싱, 알림 전송 등

    receiver = LoRaReceiver(port="COM4")

    if receiver.connect():
        try:
            receiver.receive_stream(callback=on_data_received)
        finally:
            receiver.disconnect()


# ============================================================
# 예제 6: AT 명령어로 장치 정보 확인
# ============================================================
def example_device_info():
    """장치 정보 및 현재 설정 확인"""
    config = LoRaConfig(port="COM3")

    if config.open():
        try:
            config.enter_at_mode()
            config.get_version()          # 펌웨어 버전
            config.print_current_config() # 현재 설정
            config.exit_at_mode()
        finally:
            config.close()


# ============================================================
# 예제 7: 반복 전송 (센서 데이터 시뮬레이션)
# ============================================================
def example_sensor_data():
    """주기적으로 센서 데이터를 전송하는 예제"""
    import random

    sender = LoRaSender(port="COM3")

    if sender.connect():
        try:
            for i in range(10):
                temp = round(random.uniform(20.0, 30.0), 1)
                humidity = round(random.uniform(40.0, 80.0), 1)
                message = f"SENSOR|T:{temp}|H:{humidity}|SEQ:{i}"
                sender.send_stream(message)
                time.sleep(2)  # 2초 간격
        finally:
            sender.disconnect()


if __name__ == '__main__':
    print("USB-TO-LoRa-xF 예제")
    print("-" * 40)
    print("1. 스트림 모드 송신")
    print("2. 스트림 모드 수신")
    print("3. 매개변수 설정 후 송신")
    print("4. 패킷 모드 송신")
    print("5. 콜백 수신")
    print("6. 장치 정보 확인")
    print("7. 센서 데이터 시뮬레이션")
    print()

    choice = input("예제 번호 선택: ").strip()

    examples = {
        '1': example_stream_send,
        '2': example_stream_receive,
        '3': example_with_config,
        '4': example_packet_send,
        '5': example_with_callback,
        '6': example_device_info,
        '7': example_sensor_data,
    }

    if choice in examples:
        examples[choice]()
    else:
        print("잘못된 선택입니다")
