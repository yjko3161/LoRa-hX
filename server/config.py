"""
YAML 설정 로더
config.yaml 파일에서 설정을 읽어 딕셔너리로 반환
"""

import os
import yaml

_DEFAULT_CONFIG = {
    "lora": {
        "port": "COM4",
        "baud_rate": 115200,
        "mode": "stream",
        "configure": False,
        "spreading_factor": 7,
        "bandwidth": 0,
        "power": 22,
        "channel": 18,
        "address": 0,
        "net_id": 0,
    },
    "database": {
        "type": "sqlite",
        "sqlite_path": "lora_data.db",
        "host": "localhost",
        "port": 3306,
        "name": "lora_hx",
        "user": "root",
        "password": "",
    },
    "web": {
        "host": "0.0.0.0",
        "port": 8080,
    },
    "auto_sender": {
        "sensor_port": "COM3",
        "sensor_baud": 9600,
        "lora_port": "COM4",
        "lora_baud": 115200,
        "interval": 1.0,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """base 딕셔너리에 override 값을 병합"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str = None) -> dict:
    """
    config.yaml 로드. 파일이 없으면 기본값 사용.

    Args:
        config_path: YAML 파일 경로 (None이면 자동 탐색)
    Returns:
        설정 딕셔너리
    """
    if config_path is None:
        # 실행 파일 기준 / CWD 기준 탐색
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml"),
            os.path.join(os.getcwd(), "config.yaml"),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                config_path = candidate
                break

    if config_path and os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        config = _deep_merge(_DEFAULT_CONFIG, user_config)
        print(f"[CONFIG] 설정 파일 로드: {os.path.abspath(config_path)}")
    else:
        config = _DEFAULT_CONFIG.copy()
        print("[CONFIG] config.yaml 없음 — 기본값 사용")

    return config
