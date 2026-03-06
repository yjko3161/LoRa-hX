"""
LoRa-hX 수신 서버 GUI 런처
서버 ON/OFF, COM 포트 선택, 실시간 로그, 브라우저 열기
단일 실행 파일(exe)로 빌드 가능
"""

import sys
import os
import threading
import time
import webbrowser
import logging
import io
from datetime import datetime

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

import serial.tools.list_ports

# 프로젝트 루트 (PyInstaller 호환)
if getattr(sys, "frozen", False):
    _root = sys._MEIPASS
else:
    _root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

import uvicorn

from server.config import load_config
from server.database import DatabaseManager
from server.lora_receiver import LoRaBackgroundReceiver
from server.web_app import create_app, broadcast_new_message


# ── 색상 팔레트 (lora_gui.py 통일) ───────────────────
BG_DARK = "#1a1a2e"
BG_PANEL = "#16213e"
BG_INPUT = "#0f3460"
BG_LOG = "#0a0a1a"
FG_TEXT = "#e0e0e0"
FG_DIM = "#8888aa"
TX_COLOR = "#00d4ff"
RX_COLOR = "#ff6b6b"
ACCENT = "#533483"
ACCENT_HOVER = "#7b2d8e"
BUTTON_START = "#0f9b58"
BUTTON_START_HOVER = "#14b86a"
BUTTON_STOP = "#ff5252"
CONNECTED = "#00e676"
DISCONNECTED = "#ff5252"
BORDER = "#2a2a4a"


class LogCapture(io.StringIO):
    """stdout/stderr 캡처 → GUI 로그로 전달"""

    def __init__(self, callback, original):
        super().__init__()
        self.callback = callback
        self.original = original

    def write(self, text):
        if text and text.strip():
            self.callback(text.rstrip())
        if self.original:
            self.original.write(text)
        return len(text) if text else 0

    def flush(self):
        if self.original:
            self.original.flush()


class ServerGUI:
    """LoRa-hX 수신 서버 GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LoRa-hX 수신 서버")
        self.root.geometry("780x620")
        self.root.minsize(680, 520)
        self.root.configure(bg=BG_DARK)

        # 서버 상태
        self.server_running = False
        self.uvicorn_server = None
        self.uvicorn_thread = None
        self.db_manager = None
        self.lora_receiver = None
        self.config = None
        self.rx_count = 0

        self._setup_styles()
        self._build_ui()
        self._refresh_ports()

        # stdout 캡처
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        sys.stdout = LogCapture(self._log_from_thread, self._orig_stdout)
        sys.stderr = LogCapture(self._log_from_thread, self._orig_stderr)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 상태 업데이트 타이머
        self._update_status_loop()

    # ── 스타일 ────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("Dark.TLabel", background=BG_DARK, foreground=FG_TEXT,
                         font=("맑은 고딕", 10))
        style.configure("Panel.TLabel", background=BG_PANEL, foreground=FG_TEXT,
                         font=("맑은 고딕", 10))
        style.configure("Header.TLabel", background=BG_DARK, foreground=TX_COLOR,
                         font=("맑은 고딕", 16, "bold"))
        style.configure("Status.TLabel", background=BG_PANEL, foreground=DISCONNECTED,
                         font=("맑은 고딕", 10, "bold"))
        style.configure("Dark.TLabelframe", background=BG_PANEL, foreground=FG_TEXT,
                         bordercolor=BORDER, relief="solid")
        style.configure("Dark.TLabelframe.Label", background=BG_PANEL,
                         foreground=TX_COLOR, font=("맑은 고딕", 10, "bold"))
        style.configure("Stat.TLabel", background=BG_PANEL, foreground=TX_COLOR,
                         font=("Consolas", 12, "bold"))

    # ── UI 구성 ───────────────────────────────────────
    def _build_ui(self):
        main = ttk.Frame(self.root, style="Dark.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # ── 헤더 ─────────────────────────────────────
        header = ttk.Frame(main, style="Dark.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, text="LoRa-hX 수신 서버",
                  style="Header.TLabel").pack(side=tk.LEFT)

        # ── 설정 패널 ────────────────────────────────
        settings = ttk.LabelFrame(main, text="  서버 설정  ", style="Dark.TLabelframe")
        settings.pack(fill=tk.X, pady=(0, 10))

        row = ttk.Frame(settings, style="Panel.TFrame")
        row.pack(fill=tk.X, padx=10, pady=10)

        # LoRa 포트
        ttk.Label(row, text="LoRa 포트:", style="Panel.TLabel").grid(
            row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(row, textvariable=self.port_var,
                                        width=20, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=(0, 5))

        refresh_btn = tk.Button(row, text="↻", font=("맑은 고딕", 11),
                                bg=BG_INPUT, fg=FG_TEXT, bd=0,
                                activebackground=ACCENT, cursor="hand2",
                                command=self._refresh_ports)
        refresh_btn.grid(row=0, column=2, padx=(0, 15))

        # 웹 포트
        ttk.Label(row, text="웹 포트:", style="Panel.TLabel").grid(
            row=0, column=3, padx=(0, 5), sticky=tk.W)
        self.web_port_var = tk.StringVar(value="8080")
        tk.Entry(row, textvariable=self.web_port_var, width=7,
                 bg=BG_INPUT, fg=FG_TEXT, font=("맑은 고딕", 10),
                 insertbackground=FG_TEXT, bd=0).grid(
            row=0, column=4, padx=(0, 15), ipady=3)

        # 모드
        ttk.Label(row, text="모드:", style="Panel.TLabel").grid(
            row=0, column=5, padx=(0, 5), sticky=tk.W)
        self.mode_var = tk.StringVar(value="stream")
        mode_combo = ttk.Combobox(row, textvariable=self.mode_var, width=8,
                                   values=["stream", "packet"], state="readonly")
        mode_combo.grid(row=0, column=6, padx=(0, 15))

        # LoRa 없이 실행
        self.no_lora_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row, text="LoRa 없이", variable=self.no_lora_var,
                       bg=BG_PANEL, fg=FG_TEXT, selectcolor=BG_INPUT,
                       activebackground=BG_PANEL, activeforeground=FG_TEXT,
                       font=("맑은 고딕", 9)).grid(
            row=0, column=7, padx=(0, 0))

        # ── 제어 패널 ────────────────────────────────
        ctrl = ttk.Frame(main, style="Dark.TFrame")
        ctrl.pack(fill=tk.X, pady=(0, 10))

        # 서버 시작/중지 버튼
        self.start_btn = tk.Button(
            ctrl, text="서버 시작", font=("맑은 고딕", 12, "bold"),
            bg=BUTTON_START, fg="white", activebackground=BUTTON_START_HOVER,
            bd=0, padx=30, pady=8, cursor="hand2",
            command=self._toggle_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 대시보드 열기
        self.dashboard_btn = tk.Button(
            ctrl, text="대시보드 열기", font=("맑은 고딕", 10),
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            bd=0, padx=16, pady=8, cursor="hand2",
            command=self._open_dashboard, state=tk.DISABLED)
        self.dashboard_btn.pack(side=tk.LEFT, padx=(0, 15))

        # 서버 상태
        self.status_var = tk.StringVar(value="● 서버 중지")
        self.status_label = ttk.Label(ctrl, textvariable=self.status_var,
                                       style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))

        # ── 통계 패널 ────────────────────────────────
        stat_frame = ttk.LabelFrame(main, text="  실시간 통계  ", style="Dark.TLabelframe")
        stat_frame.pack(fill=tk.X, pady=(0, 10))

        stat_inner = ttk.Frame(stat_frame, style="Panel.TFrame")
        stat_inner.pack(fill=tk.X, padx=10, pady=8)

        self.stat_total_var = tk.StringVar(value="총 수신: 0")
        self.stat_today_var = tk.StringVar(value="오늘: 0")
        self.stat_rate_var = tk.StringVar(value="분당: 0")
        self.stat_lora_var = tk.StringVar(value="LoRa: -")

        for i, (var, col) in enumerate([
            (self.stat_total_var, TX_COLOR),
            (self.stat_today_var, TX_COLOR),
            (self.stat_rate_var, TX_COLOR),
            (self.stat_lora_var, FG_DIM),
        ]):
            lbl = ttk.Label(stat_inner, textvariable=var, style="Stat.TLabel")
            lbl.configure(foreground=col)
            lbl.pack(side=tk.LEFT, padx=(0, 30))

        # ── 로그 영역 ────────────────────────────────
        log_frame = ttk.LabelFrame(main, text="  서버 로그  ", style="Dark.TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 9),
            bg=BG_LOG, fg=FG_TEXT, insertbackground=FG_TEXT,
            selectbackground=ACCENT, bd=0, padx=8, pady=8,
            state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 태그
        self.log_text.tag_configure("info", foreground="#aaaacc")
        self.log_text.tag_configure("success", foreground=CONNECTED)
        self.log_text.tag_configure("error", foreground="#ff5252")
        self.log_text.tag_configure("rx", foreground=RX_COLOR)
        self.log_text.tag_configure("system", foreground=TX_COLOR)

        # 로그 하단 버튼
        log_toolbar = ttk.Frame(log_frame, style="Panel.TFrame")
        log_toolbar.pack(fill=tk.X, padx=5, pady=(0, 5))

        tk.Button(log_toolbar, text="로그 지우기", font=("맑은 고딕", 9),
                  bg=BG_INPUT, fg=FG_DIM, bd=0, cursor="hand2",
                  activebackground=ACCENT, command=self._clear_log).pack(side=tk.RIGHT, padx=3)

    # ── 포트 관리 ─────────────────────────────────────
    def _refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [f"{p.device} - {p.description}" for p in ports]
        self.port_combo["values"] = port_list
        if port_list:
            self.port_combo.current(0)
        self._log(f"COM 포트 {len(port_list)}개 발견", "info")

    def _get_selected_port(self) -> str:
        val = self.port_var.get()
        if val:
            return val.split(" - ")[0].strip()
        return ""

    # ── 서버 제어 ─────────────────────────────────────
    def _toggle_server(self):
        if self.server_running:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        """서버 시작: DB → LoRa 수신 → uvicorn (별도 스레드)"""
        try:
            web_port = int(self.web_port_var.get())
        except ValueError:
            messagebox.showwarning("경고", "웹 포트를 올바르게 입력하세요.")
            return

        self._log("서버 시작 중...", "system")
        self._set_controls_enabled(False)

        # 설정 로드
        self.config = load_config()
        self.config["web"]["port"] = web_port
        self.config["lora"]["mode"] = self.mode_var.get()

        lora_port = self._get_selected_port()
        if lora_port:
            self.config["lora"]["port"] = lora_port

        # DB 초기화
        try:
            self.db_manager = DatabaseManager(self.config["database"])
            self.db_manager.initialize()
            self._log("DB 초기화 완료", "success")
        except Exception as e:
            self._log(f"DB 초기화 실패: {e}", "error")
            self._set_controls_enabled(True)
            return

        # LoRa 수신 콜백
        def on_lora_data(raw_data: bytes, timestamp: str):
            self.rx_count += 1
            msg = self.db_manager.save_message(raw_data)
            broadcast_new_message({
                "id": msg.id,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "raw_hex": msg.raw_hex,
                "decoded_text": msg.decoded_text,
                "byte_length": msg.byte_length,
                "source_info": msg.source_info,
            })

        # LoRa 수신 스레드
        self.lora_receiver = None
        if not self.no_lora_var.get() and lora_port:
            self.lora_receiver = LoRaBackgroundReceiver(
                self.config["lora"], on_data=on_lora_data)
            if self.lora_receiver.start():
                self._log(f"LoRa 수신 시작: {lora_port} ({self.mode_var.get()})", "success")
            else:
                self._log("LoRa 연결 실패 — 웹서버만 실행", "error")
                self.lora_receiver = None
        else:
            self._log("LoRa 수신 비활성", "info")

        # FastAPI 앱 생성
        app = create_app(self.db_manager)

        # uvicorn을 별도 스레드에서 실행
        uvi_config = uvicorn.Config(
            app,
            host=self.config["web"]["host"],
            port=web_port,
            log_level="info",
        )
        self.uvicorn_server = uvicorn.Server(uvi_config)

        self.uvicorn_thread = threading.Thread(
            target=self.uvicorn_server.run, daemon=True, name="uvicorn")
        self.uvicorn_thread.start()

        self.server_running = True
        self.rx_count = 0

        # UI 업데이트
        self.start_btn.configure(text="서버 중지", bg=BUTTON_STOP)
        self.dashboard_btn.configure(state=tk.NORMAL)
        self.status_var.set(f"● 서버 실행 중 (:{web_port})")
        self.status_label.configure(foreground=CONNECTED)

        self._log(f"웹 대시보드: http://localhost:{web_port}", "success")

    def _stop_server(self):
        """서버 중지"""
        self._log("서버 중지 중...", "system")

        # uvicorn 종료
        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True
            if self.uvicorn_thread:
                self.uvicorn_thread.join(timeout=5)
            self.uvicorn_server = None
            self.uvicorn_thread = None

        # LoRa 수신 종료
        if self.lora_receiver:
            self.lora_receiver.stop()
            self.lora_receiver = None

        # DB 닫기
        if self.db_manager:
            self.db_manager.close()
            self.db_manager = None

        self.server_running = False

        # UI 복원
        self.start_btn.configure(text="서버 시작", bg=BUTTON_START)
        self.dashboard_btn.configure(state=tk.DISABLED)
        self.status_var.set("● 서버 중지")
        self.status_label.configure(foreground=DISCONNECTED)
        self._set_controls_enabled(True)

        self._log("서버 중지 완료", "success")

    def _set_controls_enabled(self, enabled: bool):
        state = "readonly" if enabled else "disabled"
        self.port_combo.configure(state=state)
        entry_state = tk.NORMAL if enabled else tk.DISABLED
        for w in self.root.winfo_children():
            pass  # Entry는 직접 접근

    def _open_dashboard(self):
        port = self.web_port_var.get()
        webbrowser.open(f"http://localhost:{port}")

    # ── 로그 ──────────────────────────────────────────
    def _log(self, message: str, tag: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, line, tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _log_from_thread(self, text: str):
        """다른 스레드에서 호출 가능한 로그"""
        tag = "info"
        if "ERROR" in text or "error" in text.lower():
            tag = "error"
        elif "LORA RX" in text:
            tag = "rx"
        elif "OK" in text or "완료" in text or "성공" in text or "Started" in text:
            tag = "success"
        self.root.after(0, self._log, text, tag)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ── 상태 업데이트 ─────────────────────────────────
    def _update_status_loop(self):
        if self.server_running and self.db_manager:
            try:
                total = self.db_manager.get_total_count()
                today = self.db_manager.get_today_count()
                rate = self.db_manager.get_messages_per_minute(minutes=5)
                self.stat_total_var.set(f"총 수신: {total}")
                self.stat_today_var.set(f"오늘: {today}")
                self.stat_rate_var.set(f"분당: {rate:.1f}")

                if self.lora_receiver and self.lora_receiver.connected:
                    self.stat_lora_var.set(f"LoRa: 연결됨 (RX: {self.rx_count})")
                elif self.lora_receiver:
                    self.stat_lora_var.set("LoRa: 재연결 중...")
                else:
                    self.stat_lora_var.set("LoRa: 비활성")
            except Exception:
                pass

        self.root.after(2000, self._update_status_loop)

    # ── 종료 ──────────────────────────────────────────
    def _on_close(self):
        if self.server_running:
            if not messagebox.askyesno("종료 확인", "서버가 실행 중입니다. 종료하시겠습니까?"):
                return
            self._stop_server()

        # stdout 복원
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr

        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = ServerGUI()
        app.run()
    except Exception as e:
        # PyInstaller --windowed에서 에러 확인용
        import traceback
        err_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else ".", "error.log")
        with open(err_path, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        raise
