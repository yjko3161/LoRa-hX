"""
FastAPI 웹 앱 + WebSocket 브로드캐스트
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.api_routes import router as api_router, set_db_manager
from server.database import DatabaseManager

# WebSocket 연결 관리
_ws_clients: Set[WebSocket] = set()
_loop: asyncio.AbstractEventLoop = None


def create_app(db_manager: DatabaseManager) -> FastAPI:
    """FastAPI 앱 생성 및 설정"""

    app = FastAPI(title="LoRa-hX Dashboard", docs_url="/docs")

    # DB 매니저 주입
    set_db_manager(db_manager)

    # REST API 라우트
    app.include_router(api_router)

    # 정적 파일 서빙 (PyInstaller 호환)
    if getattr(sys, "frozen", False):
        static_dir = os.path.join(sys._MEIPASS, "server", "static")
    else:
        static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        _ws_clients.add(ws)
        try:
            while True:
                # 클라이언트로부터의 메시지 대기 (keep-alive)
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            _ws_clients.discard(ws)

    @app.on_event("startup")
    async def on_startup():
        global _loop
        _loop = asyncio.get_event_loop()

    return app


async def _broadcast(message: dict):
    """모든 WebSocket 클라이언트에 메시지 전송"""
    if not _ws_clients:
        return
    payload = json.dumps(message, ensure_ascii=False)
    closed = []
    for ws in _ws_clients:
        try:
            await ws.send_text(payload)
        except Exception:
            closed.append(ws)
    for ws in closed:
        _ws_clients.discard(ws)


def broadcast_new_message(msg_dict: dict):
    """
    스레드-세이프 브로드캐스트 (수신 스레드에서 호출)
    asyncio.run_coroutine_threadsafe()로 이벤트 루프에 전달
    """
    if _loop is None or _loop.is_closed():
        return
    asyncio.run_coroutine_threadsafe(_broadcast({
        "type": "new_message",
        "data": msg_dict,
    }), _loop)
