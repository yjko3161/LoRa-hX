"""
USB-TO-LoRa-xF 설정 모듈
Waveshare USB-TO-LoRa-xF (SX1262) AT 명령어 기반 설정
"""

import serial
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LoRaParams:
    """LoRa 통신 매개변수"""
    spreading_factor: int = 7       # SF7~SF12
    bandwidth: int = 0              # 0=125KHz, 1=250KHz, 2=500KHz
    coding_rate: int = 1            # 1=4/5, 2=4/6, 3=4/7, 4=4/8
    power: int = 22                 # 10~22 dBm
    net_id: int = 0                 # 0~65535
    address: int = 0                # 0~65535
    tx_channel: int = 18            # 0~80 (850~930MHz 또는 410~490MHz)
    rx_channel: int = 18            # 0~80
    mode: int = 1                   # 1=스트림, 2=패킷, 3=릴레이
    baud_rate: int = 115200         # 1200~115200
    comm: str = "8N1"               # 데이터비트/패리티/정지비트
    lbt: int = 0                    # 0=비활성, 1=활성
    rssi: int = 0                   # 0=비활성, 1=활성


class LoRaConfig:
    """USB-TO-LoRa-xF AT 명령어 설정 클래스"""

    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 1.0):
        """
        Args:
            port: 시리얼 포트 (예: 'COM3', '/dev/ttyUSB0')
            baud_rate: 통신 속도 (기본값: 115200)
            timeout: 읽기 타임아웃 (초)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        self._in_at_mode = False

    def open(self) -> bool:
        """시리얼 포트 열기"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
            print(f"[INFO] 포트 {self.port} 열림 (속도: {self.baud_rate})")
            return True
        except serial.SerialException as e:
            print(f"[ERROR] 포트 열기 실패: {e}")
            return False

    def close(self):
        """시리얼 포트 닫기"""
        if self._in_at_mode:
            self.exit_at_mode()
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[INFO] 포트 {self.port} 닫힘")

    def _send_command(self, command: str) -> str:
        """AT 명령어 전송 및 응답 수신"""
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("시리얼 포트가 열려있지 않습니다")

        cmd = f"{command}\r\n"
        self.ser.write(cmd.encode('utf-8'))
        self.ser.flush()
        time.sleep(0.3)

        response = ""
        while self.ser.in_waiting:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.05)

        response = response.strip()
        print(f"  TX: {command}")
        if response:
            print(f"  RX: {response}")
        return response

    def enter_at_mode(self) -> bool:
        """AT 명령 모드 진입 (+++ 전송)"""
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("시리얼 포트가 열려있지 않습니다")

        print("[INFO] AT 명령 모드 진입 중...")
        self.ser.write(b"+++\r\n")
        self.ser.flush()
        time.sleep(0.5)

        response = ""
        while self.ser.in_waiting:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.05)

        if "OK" in response or "AT" in response.upper() or response.strip() == "":
            self._in_at_mode = True
            print("[INFO] AT 명령 모드 진입 성공")
            return True
        else:
            print(f"[WARN] AT 모드 진입 응답: {response}")
            self._in_at_mode = True  # 응답이 없어도 시도
            return True

    def exit_at_mode(self) -> bool:
        """AT 명령 모드 종료"""
        response = self._send_command("AT+EXIT")
        self._in_at_mode = False
        print("[INFO] AT 명령 모드 종료")
        return True

    def get_version(self) -> str:
        """펌웨어 버전 확인"""
        return self._send_command("AT+VER")

    def get_help(self) -> str:
        """AT 명령어 도움말"""
        return self._send_command("AT+HELP")

    def set_spreading_factor(self, sf: int) -> str:
        """확산 인자 설정 (7~12)"""
        if not 7 <= sf <= 12:
            raise ValueError("확산 인자는 7~12 범위여야 합니다")
        return self._send_command(f"AT+SF={sf}")

    def set_bandwidth(self, bw: int) -> str:
        """대역폭 설정 (0=125KHz, 1=250KHz, 2=500KHz)"""
        if bw not in (0, 1, 2):
            raise ValueError("대역폭은 0, 1, 2 중 하나여야 합니다")
        return self._send_command(f"AT+BW={bw}")

    def set_coding_rate(self, cr: int) -> str:
        """코딩률 설정 (1=4/5, 2=4/6, 3=4/7, 4=4/8)"""
        if not 1 <= cr <= 4:
            raise ValueError("코딩률은 1~4 범위여야 합니다")
        return self._send_command(f"AT+CR={cr}")

    def set_power(self, power: int) -> str:
        """RF 출력 전력 설정 (10~22 dBm)"""
        if not 10 <= power <= 22:
            raise ValueError("출력 전력은 10~22 dBm 범위여야 합니다")
        return self._send_command(f"AT+PWR={power}")

    def set_net_id(self, net_id: int) -> str:
        """네트워크 ID 설정 (0~65535)"""
        if not 0 <= net_id <= 65535:
            raise ValueError("네트워크 ID는 0~65535 범위여야 합니다")
        return self._send_command(f"AT+NETID={net_id}")

    def set_address(self, addr: int) -> str:
        """장치 주소 설정 (0~65535)"""
        if not 0 <= addr <= 65535:
            raise ValueError("주소는 0~65535 범위여야 합니다")
        return self._send_command(f"AT+ADDR={addr}")

    def set_tx_channel(self, ch: int) -> str:
        """송신 채널 설정 (0~80)"""
        if not 0 <= ch <= 80:
            raise ValueError("채널은 0~80 범위여야 합니다")
        return self._send_command(f"AT+TXCH={ch}")

    def set_rx_channel(self, ch: int) -> str:
        """수신 채널 설정 (0~80)"""
        if not 0 <= ch <= 80:
            raise ValueError("채널은 0~80 범위여야 합니다")
        return self._send_command(f"AT+RXCH={ch}")

    def set_mode(self, mode: int) -> str:
        """동작 모드 설정 (1=스트림, 2=패킷, 3=릴레이)"""
        if mode not in (1, 2, 3):
            raise ValueError("모드는 1, 2, 3 중 하나여야 합니다")
        return self._send_command(f"AT+MODE={mode}")

    def set_baud_rate(self, baud: int) -> str:
        """시리얼 통신 속도 설정"""
        valid_bauds = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        if baud not in valid_bauds:
            raise ValueError(f"유효한 속도: {valid_bauds}")
        return self._send_command(f"AT+BAUD={baud}")

    def set_rssi(self, enable: int) -> str:
        """RSSI 출력 활성화/비활성화 (0=비활성, 1=활성)"""
        if enable not in (0, 1):
            raise ValueError("RSSI는 0 또는 1이어야 합니다")
        return self._send_command(f"AT+RSSI={enable}")

    def set_lbt(self, enable: int) -> str:
        """LBT (Listen Before Talk) 활성화/비활성화"""
        if enable not in (0, 1):
            raise ValueError("LBT는 0 또는 1이어야 합니다")
        return self._send_command(f"AT+LBT={enable}")

    def restore_factory(self) -> str:
        """공장 초기화"""
        return self._send_command("AT+RESTORE=1")

    def apply_params(self, params: LoRaParams) -> bool:
        """LoRaParams 객체로 일괄 설정 적용"""
        if not self._in_at_mode:
            self.enter_at_mode()

        try:
            print("[INFO] LoRa 매개변수 설정 중...")
            self.set_mode(params.mode)
            self.set_spreading_factor(params.spreading_factor)
            self.set_bandwidth(params.bandwidth)
            self.set_coding_rate(params.coding_rate)
            self.set_power(params.power)
            self.set_net_id(params.net_id)
            self.set_address(params.address)
            self.set_tx_channel(params.tx_channel)
            self.set_rx_channel(params.rx_channel)
            self.set_rssi(params.rssi)
            self.set_lbt(params.lbt)
            self.set_baud_rate(params.baud_rate)
            print("[INFO] 모든 매개변수 설정 완료")
            return True
        except Exception as e:
            print(f"[ERROR] 매개변수 설정 실패: {e}")
            return False

    def print_current_config(self):
        """현재 설정 정보 출력 (AT+AllP 이용)"""
        if not self._in_at_mode:
            self.enter_at_mode()
        response = self._send_command("AT+AllP=?")
        print(f"[INFO] 현재 설정: {response}")
        return response
