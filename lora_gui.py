"""
USB-TO-LoRa-xF GUI 애플리케이션
tkinter 기반 송수신 통합 GUI

사용법:
    python lora_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime


class LoRaGUI:
    """USB-TO-LoRa-xF 통합 GUI"""

    # ── 색상 팔레트 ──────────────────────────────────────────
    BG_DARK = "#1a1a2e"
    BG_PANEL = "#16213e"
    BG_INPUT = "#0f3460"
    BG_LOG = "#0a0a1a"
    FG_TEXT = "#e0e0e0"
    FG_DIM = "#8888aa"
    TX_COLOR = "#00d4ff"       # 송신: 시안
    RX_COLOR = "#ff6b6b"       # 수신: 코랄 레드
    ACCENT = "#533483"
    ACCENT_HOVER = "#7b2d8e"
    BUTTON_SEND = "#0f9b58"
    BUTTON_SEND_HOVER = "#14b86a"
    CONNECTED = "#00e676"
    DISCONNECTED = "#ff5252"
    BORDER = "#2a2a4a"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("USB-TO-LoRa-xF 통신 도구")
        self.root.geometry("960x720")
        self.root.minsize(800, 600)
        self.root.configure(bg=self.BG_DARK)

        # 상태
        self.ser = None
        self.running = False
        self.rx_thread = None
        self.tx_count = 0
        self.rx_count = 0
        self.log_file = None

        # 스타일
        self._setup_styles()
        self._build_ui()
        self._refresh_ports()

        # 닫기 핸들러
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 스타일 설정 ──────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Dark.TFrame", background=self.BG_DARK)
        style.configure("Panel.TFrame", background=self.BG_PANEL)
        style.configure("Dark.TLabel", background=self.BG_DARK, foreground=self.FG_TEXT,
                         font=("맑은 고딕", 10))
        style.configure("Panel.TLabel", background=self.BG_PANEL, foreground=self.FG_TEXT,
                         font=("맑은 고딕", 10))
        style.configure("Header.TLabel", background=self.BG_DARK, foreground=self.TX_COLOR,
                         font=("맑은 고딕", 14, "bold"))
        style.configure("Status.TLabel", background=self.BG_PANEL, foreground=self.DISCONNECTED,
                         font=("맑은 고딕", 10, "bold"))

        style.configure("Dark.TLabelframe", background=self.BG_PANEL, foreground=self.FG_TEXT,
                         bordercolor=self.BORDER, relief="solid")
        style.configure("Dark.TLabelframe.Label", background=self.BG_PANEL,
                         foreground=self.TX_COLOR, font=("맑은 고딕", 10, "bold"))

        style.configure("Connect.TButton", font=("맑은 고딕", 10, "bold"), padding=6)
        style.configure("Send.TButton", font=("맑은 고딕", 11, "bold"), padding=8)
        style.configure("Dark.TCombobox", fieldbackground=self.BG_INPUT, foreground=self.FG_TEXT)

        style.configure("TX.TLabel", background=self.BG_PANEL, foreground=self.TX_COLOR,
                         font=("맑은 고딕", 12, "bold"))
        style.configure("RX.TLabel", background=self.BG_PANEL, foreground=self.RX_COLOR,
                         font=("맑은 고딕", 12, "bold"))

    # ── UI 구성 ──────────────────────────────────────────────
    def _build_ui(self):
        # 최상위 프레임
        main = ttk.Frame(self.root, style="Dark.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ── 상단: 타이틀 ────────────────────────────────────
        title_frame = ttk.Frame(main, style="Dark.TFrame")
        title_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(title_frame, text="📡 USB-TO-LoRa-xF 통신 도구",
                  style="Header.TLabel").pack(side=tk.LEFT)

        # ── 연결 패널 ───────────────────────────────────────
        conn_frame = ttk.LabelFrame(main, text="  연결 설정  ", style="Dark.TLabelframe")
        conn_frame.pack(fill=tk.X, pady=(0, 8))

        conn_inner = ttk.Frame(conn_frame, style="Panel.TFrame")
        conn_inner.pack(fill=tk.X, padx=10, pady=8)

        # 포트
        ttk.Label(conn_inner, text="COM 포트:", style="Panel.TLabel").grid(
            row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_inner, textvariable=self.port_var,
                                        width=15, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=(0, 5))

        refresh_btn = tk.Button(conn_inner, text="🔄", font=("맑은 고딕", 10),
                                bg=self.BG_INPUT, fg=self.FG_TEXT, bd=0,
                                activebackground=self.ACCENT, cursor="hand2",
                                command=self._refresh_ports)
        refresh_btn.grid(row=0, column=2, padx=(0, 15))

        # 속도
        ttk.Label(conn_inner, text="속도:", style="Panel.TLabel").grid(
            row=0, column=3, padx=(0, 5), sticky=tk.W)
        self.baud_var = tk.StringVar(value="115200")
        baud_combo = ttk.Combobox(conn_inner, textvariable=self.baud_var, width=10,
                                   values=["9600", "19200", "38400", "57600", "115200"],
                                   state="readonly")
        baud_combo.grid(row=0, column=4, padx=(0, 15))

        # 모드
        ttk.Label(conn_inner, text="모드:", style="Panel.TLabel").grid(
            row=0, column=5, padx=(0, 5), sticky=tk.W)
        self.mode_var = tk.StringVar(value="스트림")
        mode_combo = ttk.Combobox(conn_inner, textvariable=self.mode_var, width=8,
                                   values=["스트림", "패킷"], state="readonly")
        mode_combo.grid(row=0, column=6, padx=(0, 15))

        # 연결 버튼
        self.connect_btn = tk.Button(
            conn_inner, text="🔌 연결", font=("맑은 고딕", 10, "bold"),
            bg=self.ACCENT, fg="white", activebackground=self.ACCENT_HOVER,
            bd=0, padx=16, pady=4, cursor="hand2",
            command=self._toggle_connection)
        self.connect_btn.grid(row=0, column=7, padx=(5, 0))

        # 상태
        self.status_var = tk.StringVar(value="● 연결 안됨")
        self.status_label = ttk.Label(conn_inner, textvariable=self.status_var,
                                       style="Status.TLabel")
        self.status_label.grid(row=0, column=8, padx=(15, 0))

        # ── LoRa 설정 패널 (접이식) ─────────────────────────
        self.settings_visible = False
        settings_toggle = tk.Button(
            main, text="⚙️ LoRa 설정 (AT 명령어)", font=("맑은 고딕", 9),
            bg=self.BG_PANEL, fg=self.FG_DIM, bd=0, anchor=tk.W,
            activebackground=self.BG_DARK, cursor="hand2",
            command=self._toggle_settings)
        settings_toggle.pack(fill=tk.X, pady=(0, 2))

        self.settings_frame = ttk.LabelFrame(main, text="  LoRa 매개변수  ",
                                              style="Dark.TLabelframe")
        # 숨김 상태로 시작

        settings_inner = ttk.Frame(self.settings_frame, style="Panel.TFrame")
        settings_inner.pack(fill=tk.X, padx=10, pady=8)

        # SF
        ttk.Label(settings_inner, text="SF:", style="Panel.TLabel").grid(
            row=0, column=0, padx=(0, 3), sticky=tk.W)
        self.sf_var = tk.StringVar(value="7")
        ttk.Combobox(settings_inner, textvariable=self.sf_var, width=4,
                      values=["7", "8", "9", "10", "11", "12"],
                      state="readonly").grid(row=0, column=1, padx=(0, 10))

        # BW
        ttk.Label(settings_inner, text="BW:", style="Panel.TLabel").grid(
            row=0, column=2, padx=(0, 3), sticky=tk.W)
        self.bw_var = tk.StringVar(value="125K")
        ttk.Combobox(settings_inner, textvariable=self.bw_var, width=6,
                      values=["125K", "250K", "500K"],
                      state="readonly").grid(row=0, column=3, padx=(0, 10))

        # 출력
        ttk.Label(settings_inner, text="출력(dBm):", style="Panel.TLabel").grid(
            row=0, column=4, padx=(0, 3), sticky=tk.W)
        self.power_var = tk.StringVar(value="22")
        ttk.Combobox(settings_inner, textvariable=self.power_var, width=4,
                      values=[str(i) for i in range(10, 23)],
                      state="readonly").grid(row=0, column=5, padx=(0, 10))

        # 채널
        ttk.Label(settings_inner, text="채널:", style="Panel.TLabel").grid(
            row=0, column=6, padx=(0, 3), sticky=tk.W)
        self.ch_var = tk.StringVar(value="18")
        tk.Spinbox(settings_inner, textvariable=self.ch_var, from_=0, to=80,
                    width=4, bg=self.BG_INPUT, fg=self.FG_TEXT,
                    buttonbackground=self.BG_INPUT).grid(row=0, column=7, padx=(0, 10))

        # 주소
        ttk.Label(settings_inner, text="주소:", style="Panel.TLabel").grid(
            row=0, column=8, padx=(0, 3), sticky=tk.W)
        self.addr_var = tk.StringVar(value="0")
        tk.Spinbox(settings_inner, textvariable=self.addr_var, from_=0, to=65535,
                    width=6, bg=self.BG_INPUT, fg=self.FG_TEXT,
                    buttonbackground=self.BG_INPUT).grid(row=0, column=9, padx=(0, 10))

        # 설정 적용 버튼
        apply_btn = tk.Button(
            settings_inner, text="적용", font=("맑은 고딕", 9, "bold"),
            bg=self.ACCENT, fg="white", bd=0, padx=12, pady=2,
            activebackground=self.ACCENT_HOVER, cursor="hand2",
            command=self._apply_settings)
        apply_btn.grid(row=0, column=10, padx=(5, 0))

        # ── 통신 로그 ───────────────────────────────────────
        log_frame = ttk.LabelFrame(main, text="  통신 로그  ", style="Dark.TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=self.BG_LOG, fg=self.FG_TEXT, insertbackground=self.FG_TEXT,
            selectbackground=self.ACCENT, bd=0, padx=8, pady=8,
            state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 태그 설정
        self.log_text.tag_configure("tx", foreground=self.TX_COLOR, font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("rx", foreground=self.RX_COLOR, font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("info", foreground="#aaaacc")
        self.log_text.tag_configure("error", foreground="#ff5252", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("hex", foreground="#888899", font=("Consolas", 9))
        self.log_text.tag_configure("system", foreground="#7c4dff")

        # ── 로그 도구 버튼 ──────────────────────────────────
        log_toolbar = ttk.Frame(log_frame, style="Panel.TFrame")
        log_toolbar.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.tx_count_var = tk.StringVar(value="📡 TX: 0")
        self.rx_count_var = tk.StringVar(value="📥 RX: 0")

        ttk.Label(log_toolbar, textvariable=self.tx_count_var,
                  style="TX.TLabel").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(log_toolbar, textvariable=self.rx_count_var,
                  style="RX.TLabel").pack(side=tk.LEFT, padx=(0, 15))

        clear_btn = tk.Button(log_toolbar, text="🗑️ 지우기", font=("맑은 고딕", 9),
                              bg=self.BG_INPUT, fg=self.FG_DIM, bd=0, cursor="hand2",
                              activebackground=self.ACCENT, command=self._clear_log)
        clear_btn.pack(side=tk.RIGHT, padx=3)

        save_btn = tk.Button(log_toolbar, text="💾 저장", font=("맑은 고딕", 9),
                             bg=self.BG_INPUT, fg=self.FG_DIM, bd=0, cursor="hand2",
                             activebackground=self.ACCENT, command=self._save_log)
        save_btn.pack(side=tk.RIGHT, padx=3)

        # ── 하단: 전송 영역 ─────────────────────────────────
        send_frame = ttk.LabelFrame(main, text="  메시지 전송  ", style="Dark.TLabelframe")
        send_frame.pack(fill=tk.X, pady=(0, 0))

        send_inner = ttk.Frame(send_frame, style="Panel.TFrame")
        send_inner.pack(fill=tk.X, padx=10, pady=8)

        # 스트림 모드 입력
        self.stream_frame = ttk.Frame(send_inner, style="Panel.TFrame")
        self.stream_frame.pack(fill=tk.X)

        ttk.Label(self.stream_frame, text="📡 메시지:", style="Panel.TLabel").pack(
            side=tk.LEFT, padx=(0, 5))
        self.msg_entry = tk.Entry(
            self.stream_frame, font=("맑은 고딕", 11),
            bg=self.BG_INPUT, fg=self.FG_TEXT, insertbackground=self.FG_TEXT,
            bd=0, relief=tk.FLAT)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        self.msg_entry.bind("<Return>", lambda e: self._send_message())

        self.send_btn = tk.Button(
            self.stream_frame, text="📡 전송 (Enter)", font=("맑은 고딕", 11, "bold"),
            bg=self.BUTTON_SEND, fg="white", activebackground=self.BUTTON_SEND_HOVER,
            bd=0, padx=20, pady=6, cursor="hand2",
            command=self._send_message, state=tk.DISABLED)
        self.send_btn.pack(side=tk.RIGHT)

        # 패킷 모드 입력
        self.packet_frame = ttk.Frame(send_inner, style="Panel.TFrame")

        pkt_row1 = ttk.Frame(self.packet_frame, style="Panel.TFrame")
        pkt_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(pkt_row1, text="대상 주소:", style="Panel.TLabel").pack(side=tk.LEFT, padx=(0, 3))
        self.pkt_addr_var = tk.StringVar(value="65535")
        tk.Entry(pkt_row1, textvariable=self.pkt_addr_var, width=8,
                 bg=self.BG_INPUT, fg=self.FG_TEXT, font=("맑은 고딕", 10),
                 insertbackground=self.FG_TEXT, bd=0).pack(side=tk.LEFT, padx=(0, 10), ipady=3)

        ttk.Label(pkt_row1, text="채널:", style="Panel.TLabel").pack(side=tk.LEFT, padx=(0, 3))
        self.pkt_ch_var = tk.StringVar(value="18")
        tk.Entry(pkt_row1, textvariable=self.pkt_ch_var, width=4,
                 bg=self.BG_INPUT, fg=self.FG_TEXT, font=("맑은 고딕", 10),
                 insertbackground=self.FG_TEXT, bd=0).pack(side=tk.LEFT, padx=(0, 10), ipady=3)

        ttk.Label(pkt_row1, text="HEX 데이터:", style="Panel.TLabel").pack(side=tk.LEFT, padx=(0, 3))
        self.pkt_data_var = tk.StringVar(value="")
        pkt_entry = tk.Entry(pkt_row1, textvariable=self.pkt_data_var,
                             bg=self.BG_INPUT, fg=self.FG_TEXT, font=("Consolas", 10),
                             insertbackground=self.FG_TEXT, bd=0)
        pkt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=3)
        pkt_entry.bind("<Return>", lambda e: self._send_packet())

        self.pkt_send_btn = tk.Button(
            pkt_row1, text="📡 전송", font=("맑은 고딕", 10, "bold"),
            bg=self.BUTTON_SEND, fg="white", activebackground=self.BUTTON_SEND_HOVER,
            bd=0, padx=16, pady=3, cursor="hand2",
            command=self._send_packet, state=tk.DISABLED)
        self.pkt_send_btn.pack(side=tk.RIGHT)

        # 모드 변경 이벤트
        self.mode_var.trace_add("write", self._on_mode_changed)
        self._on_mode_changed()

    # ── 포트 관련 ────────────────────────────────────────────
    def _refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [f"{p.device} - {p.description}" for p in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
        self._log("시스템", f"COM 포트 {len(port_list)}개 발견", "system")

    def _get_selected_port(self) -> str:
        val = self.port_var.get()
        if val:
            return val.split(" - ")[0].strip()
        return ""

    # ── 연결 ─────────────────────────────────────────────────
    def _toggle_connection(self):
        if self.ser and self.ser.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self._get_selected_port()
        baud = int(self.baud_var.get())

        if not port:
            messagebox.showwarning("경고", "COM 포트를 선택하세요.")
            return

        try:
            self.ser = serial.Serial(
                port=port, baudrate=baud,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, timeout=0.1)

            self.running = True
            self.rx_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.rx_thread.start()

            # UI 업데이트
            self.connect_btn.configure(text="🔌 연결 해제", bg=self.DISCONNECTED)
            self.status_var.set(f"● 연결됨 ({port})")
            self.status_label.configure(foreground=self.CONNECTED)
            self.send_btn.configure(state=tk.NORMAL)
            self.pkt_send_btn.configure(state=tk.NORMAL)
            self.port_combo.configure(state=tk.DISABLED)

            self._log("시스템", f"{port} 연결 성공 (속도: {baud})", "system")

        except serial.SerialException as e:
            messagebox.showerror("연결 오류", f"포트 열기 실패:\n{e}")

    def _disconnect(self):
        self.running = False
        if self.rx_thread:
            self.rx_thread.join(timeout=1)

        if self.ser and self.ser.is_open:
            port = self.ser.port
            self.ser.close()
            self._log("시스템", f"{port} 연결 해제", "system")

        self.ser = None
        self.connect_btn.configure(text="🔌 연결", bg=self.ACCENT)
        self.status_var.set("● 연결 안됨")
        self.status_label.configure(foreground=self.DISCONNECTED)
        self.send_btn.configure(state=tk.DISABLED)
        self.pkt_send_btn.configure(state=tk.DISABLED)
        self.port_combo.configure(state="readonly")

    # ── 수신 루프 ────────────────────────────────────────────
    def _receive_loop(self):
        while self.running:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    time.sleep(0.05)
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        self.rx_count += 1
                        text = data.decode('utf-8', errors='replace')
                        hex_str = ' '.join(f'{b:02X}' for b in data)

                        self.root.after(0, self._log, "📥 RX ←",
                                        f"{text}", "rx")
                        self.root.after(0, self._log, "       ",
                                        f"HEX: {hex_str} ({len(data)}B)", "hex")
                        self.root.after(0, self._update_counts)
                else:
                    time.sleep(0.01)
            except Exception:
                if self.running:
                    time.sleep(0.05)

    # ── 송신 ─────────────────────────────────────────────────
    def _send_message(self):
        """스트림 모드 메시지 전송"""
        if not self.ser or not self.ser.is_open:
            return

        message = self.msg_entry.get().strip()
        if not message:
            return

        try:
            data = message.encode('utf-8')
            self.ser.write(data)
            self.ser.flush()
            self.tx_count += 1
            hex_str = ' '.join(f'{b:02X}' for b in data)

            self._log("📡 TX →", f"{message}", "tx")
            self._log("       ", f"HEX: {hex_str} ({len(data)}B)", "hex")
            self._update_counts()
            self.msg_entry.delete(0, tk.END)

        except Exception as e:
            self._log("ERROR", f"전송 실패: {e}", "error")

    def _send_packet(self):
        """패킷 모드 데이터 전송"""
        if not self.ser or not self.ser.is_open:
            return

        try:
            addr = int(self.pkt_addr_var.get())
            ch = int(self.pkt_ch_var.get())
            hex_data = self.pkt_data_var.get().strip().replace(" ", "")

            if not hex_data:
                messagebox.showwarning("경고", "HEX 데이터를 입력하세요.")
                return

            addr_bytes = addr.to_bytes(2, byteorder='big')
            ch_byte = ch.to_bytes(1, byteorder='big')
            payload = bytes.fromhex(hex_data)
            packet = addr_bytes + ch_byte + payload

            self.ser.write(packet)
            self.ser.flush()
            self.tx_count += 1

            pkt_hex = ' '.join(f'{b:02X}' for b in packet)
            self._log("📡 TX →", f"주소: {addr}(0x{addr:04X}) 채널: {ch}", "tx")
            self._log("       ", f"HEX: {pkt_hex} ({len(packet)}B)", "hex")
            self._update_counts()
            self.pkt_data_var.set("")

        except ValueError as e:
            self._log("ERROR", f"입력 오류: {e}", "error")
        except Exception as e:
            self._log("ERROR", f"전송 실패: {e}", "error")

    # ── AT 설정 ──────────────────────────────────────────────
    def _toggle_settings(self):
        if self.settings_visible:
            self.settings_frame.pack_forget()
            self.settings_visible = False
        else:
            # log_frame 앞에 삽입
            self.settings_frame.pack(fill=tk.X, pady=(0, 4),
                                      before=self.settings_frame.master.winfo_children()[3])
            self.settings_visible = True

    def _apply_settings(self):
        """AT 명령으로 설정 적용"""
        if not self.ser or not self.ser.is_open:
            messagebox.showwarning("경고", "먼저 장치를 연결하세요.")
            return

        try:
            bw_map = {"125K": 0, "250K": 1, "500K": 2}
            mode_map = {"스트림": 1, "패킷": 2}

            self._log("시스템", "AT 설정 적용 중...", "system")

            # AT 모드 진입
            self.ser.write(b"+++\r\n")
            self.ser.flush()
            time.sleep(0.5)
            self.ser.read(self.ser.in_waiting)  # 응답 비우기

            commands = [
                f"AT+MODE={mode_map.get(self.mode_var.get(), 1)}",
                f"AT+SF={self.sf_var.get()}",
                f"AT+BW={bw_map.get(self.bw_var.get(), 0)}",
                f"AT+PWR={self.power_var.get()}",
                f"AT+TXCH={self.ch_var.get()}",
                f"AT+RXCH={self.ch_var.get()}",
                f"AT+ADDR={self.addr_var.get()}",
            ]

            for cmd in commands:
                self.ser.write(f"{cmd}\r\n".encode())
                self.ser.flush()
                time.sleep(0.2)
                resp = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore').strip()
                self._log("  AT", f"{cmd}  →  {resp}", "info")

            # AT 모드 종료
            self.ser.write(b"AT+EXIT\r\n")
            self.ser.flush()
            time.sleep(0.3)
            self.ser.read(self.ser.in_waiting)

            self._log("시스템", "AT 설정 적용 완료!", "system")

        except Exception as e:
            self._log("ERROR", f"설정 실패: {e}", "error")

    # ── 모드 전환 ────────────────────────────────────────────
    def _on_mode_changed(self, *args):
        mode = self.mode_var.get()
        if mode == "패킷":
            self.stream_frame.pack_forget()
            self.packet_frame.pack(fill=tk.X)
        else:
            self.packet_frame.pack_forget()
            self.stream_frame.pack(fill=tk.X)

    # ── 로그 ─────────────────────────────────────────────────
    def _log(self, prefix: str, message: str, tag: str = "info"):
        ts = datetime.now().strftime('%H:%M:%S')
        line = f"[{ts}] {prefix}  {message}\n"

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, line, tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _update_counts(self):
        self.tx_count_var.set(f"📡 TX: {self.tx_count}")
        self.rx_count_var.set(f"📥 RX: {self.rx_count}")

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.tx_count = 0
        self.rx_count = 0
        self._update_counts()

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("로그 파일", "*.log"), ("텍스트 파일", "*.txt")],
            initialfile=f"lora_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        if path:
            content = self.log_text.get(1.0, tk.END)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._log("시스템", f"로그 저장: {path}", "system")

    # ── 종료 ─────────────────────────────────────────────────
    def _on_close(self):
        self._disconnect()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = LoRaGUI()
    app.run()
