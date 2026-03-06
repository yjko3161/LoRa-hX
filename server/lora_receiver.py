"""
백그라운드 LoRa 수신 루프
daemon 스레드에서 시리얼 폴링 → 콜백으로 데이터 전달
"""

import time
import threading
from typing import Callable, Optional

import serial

from lora_config import LoRaConfig, LoRaParams


class LoRaBackgroundReceiver:
    """백그라운드 시리얼 수신기 (daemon thread)"""

    def __init__(self, config: dict, on_data: Callable[[bytes, str], None]):
        """
        Args:
            config: lora 설정 딕셔너리 (config.yaml의 lora 섹션)
            on_data: 콜백 함수 (raw_bytes, timestamp_str) -> None
        """
        self.port = config.get("port", "COM4")
        self.baud_rate = config.get("baud_rate", 115200)
        self.mode = config.get("mode", "stream")
        self.lora_config_dict = config
        self.on_data = on_data

        self._lora_config: Optional[LoRaConfig] = None
        self._ser: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        self.received_count = 0

    @property
    def connected(self) -> bool:
        return self._connected and self._ser is not None and self._ser.is_open

    def start(self):
        """연결 + 수신 스레드 시작"""
        if not self._connect():
            print("[LORA] 연결 실패 — 수신 스레드를 시작하지 않습니다")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._receive_loop, daemon=True, name="lora-rx")
        self._thread.start()
        print(f"[LORA] 수신 스레드 시작 (port={self.port}, mode={self.mode})")
        return True

    def stop(self):
        """수신 중지 + 연결 해제"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._lora_config:
            self._lora_config.close()
        self._connected = False
        print(f"[LORA] 수신 중지 (총 {self.received_count}건 수신)")

    def _connect(self) -> bool:
        """LoRa 장치 연결 및 설정"""
        try:
            self._lora_config = LoRaConfig(self.port, self.baud_rate, timeout=0.5)
            if not self._lora_config.open():
                return False
            self._ser = self._lora_config.ser

            # 설정 적용 (configure: true 시)
            if self.lora_config_dict.get("configure", False):
                params = LoRaParams()
                params.mode = 1 if self.mode == "stream" else 2
                params.spreading_factor = self.lora_config_dict.get("spreading_factor", 7)
                params.bandwidth = self.lora_config_dict.get("bandwidth", 0)
                params.power = self.lora_config_dict.get("power", 22)
                ch = self.lora_config_dict.get("channel", 18)
                params.tx_channel = ch
                params.rx_channel = ch
                params.address = self.lora_config_dict.get("address", 0)
                params.net_id = self.lora_config_dict.get("net_id", 0)

                self._lora_config.enter_at_mode()
                self._lora_config.apply_params(params)
                self._lora_config.exit_at_mode()
                time.sleep(0.5)

            self._connected = True
            return True

        except Exception as e:
            print(f"[LORA] 연결 오류: {e}")
            return False

    def _receive_loop(self):
        """시리얼 폴링 루프 (receiver.py:88-109 패턴)"""
        while self._running:
            try:
                if self._ser and self._ser.is_open and self._ser.in_waiting > 0:
                    time.sleep(0.05)  # 패킷 완성 대기
                    data = self._ser.read(self._ser.in_waiting)

                    if data:
                        self.received_count += 1
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        hex_str = " ".join(f"{b:02X}" for b in data)
                        print(f"[LORA RX] #{self.received_count} ({len(data)}B) {hex_str}")

                        try:
                            self.on_data(data, timestamp)
                        except Exception as e:
                            print(f"[LORA] 콜백 오류: {e}")
                else:
                    time.sleep(0.01)

            except serial.SerialException as e:
                print(f"[LORA] 시리얼 오류: {e}")
                self._connected = False
                # 재연결 시도
                time.sleep(2)
                if self._running:
                    print("[LORA] 재연결 시도...")
                    if self._connect():
                        print("[LORA] 재연결 성공")
                    else:
                        print("[LORA] 재연결 실패 — 2초 후 재시도")

            except Exception as e:
                if self._running:
                    print(f"[LORA] 수신 루프 오류: {e}")
                    time.sleep(0.1)
