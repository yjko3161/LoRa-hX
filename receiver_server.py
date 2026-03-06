"""
LoRa-hX 수신 서버 — 메인 진입점
LoRa 수신 (daemon thread) + DB 저장 + 웹 대시보드 (uvicorn)
"""

import sys
import os
import argparse
import signal

# 프로젝트 루트를 sys.path에 추가 (PyInstaller 빌드 호환)
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

import uvicorn

from server.config import load_config
from server.database import DatabaseManager
from server.lora_receiver import LoRaBackgroundReceiver
from server.web_app import create_app, broadcast_new_message


def main():
    parser = argparse.ArgumentParser(description="LoRa-hX 수신 서버")
    parser.add_argument("--config", "-c", default=None, help="config.yaml 경로")
    parser.add_argument("--port", "-p", type=int, default=None, help="웹서버 포트 (config.yaml 오버라이드)")
    parser.add_argument("--lora-port", default=None, help="LoRa 시리얼 포트 (config.yaml 오버라이드)")
    parser.add_argument("--no-lora", action="store_true", help="LoRa 수신 없이 웹서버만 실행")
    args = parser.parse_args()

    # ── 설정 로드 ─────────────────────────────
    config = load_config(args.config)

    # CLI 오버라이드
    if args.port:
        config["web"]["port"] = args.port
    if args.lora_port:
        config["lora"]["port"] = args.lora_port

    web_host = config["web"]["host"]
    web_port = config["web"]["port"]

    # ── DB 초기화 ─────────────────────────────
    db_manager = DatabaseManager(config["database"])
    db_manager.initialize()

    # ── LoRa 수신 콜백 ───────────────────────
    def on_lora_data(raw_data: bytes, timestamp: str):
        """수신 데이터 → DB 저장 + WebSocket 브로드캐스트"""
        msg = db_manager.save_message(raw_data)
        broadcast_new_message({
            "id": msg.id,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_hex": msg.raw_hex,
            "decoded_text": msg.decoded_text,
            "byte_length": msg.byte_length,
            "source_info": msg.source_info,
        })

    # ── LoRa 수신 스레드 시작 ─────────────────
    receiver = None
    if not args.no_lora:
        receiver = LoRaBackgroundReceiver(config["lora"], on_data=on_lora_data)
        if not receiver.start():
            print("[WARN] LoRa 연결 실패 — 웹서버만 실행합니다")
            receiver = None

    # ── FastAPI 앱 생성 ───────────────────────
    app = create_app(db_manager)

    # ── 종료 핸들링 ───────────────────────────
    def shutdown(sig=None, frame=None):
        print("\n[INFO] 서버 종료 중...")
        if receiver:
            receiver.stop()
        db_manager.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ── 서버 시작 ─────────────────────────────
    print("=" * 60)
    print("  LoRa-hX 수신 서버")
    print(f"  웹 대시보드: http://localhost:{web_port}")
    if receiver:
        print(f"  LoRa 포트: {config['lora']['port']} ({config['lora']['mode']} 모드)")
    else:
        print("  LoRa: 비활성 (--no-lora 또는 연결 실패)")
    print(f"  DB: {config['database']['type']} ({config['database'].get('sqlite_path', '')})")
    print("  Ctrl+C로 종료")
    print("=" * 60)

    uvicorn.run(app, host=web_host, port=web_port, log_level="info")


if __name__ == "__main__":
    main()
