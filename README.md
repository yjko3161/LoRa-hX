# USB-TO-LoRa-xF Python 통신 도구

Waveshare **USB-TO-LoRa-xF** (SX1262) 기반 LoRa 송수신 + 수신 서버 + 웹 대시보드 통합 도구입니다.

---

## 프로젝트 구조

```
LoRa-hX/
│
│  ── 기본 도구 ──────────────────────────
├── lora_config.py           # AT 명령어 설정 모듈 (LoRaConfig, LoRaParams)
├── sender.py                # 송신기 (스트림/패킷 모드, CLI)
├── receiver.py              # 수신기 (스트림/패킷 모드, CLI)
├── monitor.py               # 양방향 모니터 (송수신 동시)
├── lora_gui.py              # tkinter 기반 송수신 GUI
├── examples.py              # 사용 예제
├── diagnose.py              # 장치 진단
├── requirements.txt         # 기본 의존성
│
│  ── 수신 서버 + 대시보드 ───────────────
├── server_gui.py            # 수신 서버 GUI 런처 (메인 실행 파일)
├── receiver_server.py       # 수신 서버 CLI 진입점
├── auto_sender.py           # 센서→LoRa 자동 중계기
├── config.yaml              # 서버 설정 (DB, 포트, 웹서버)
├── requirements-server.txt  # 서버 의존성
│
├── server/
│   ├── __init__.py
│   ├── config.py            # YAML 설정 로더
│   ├── database.py          # Peewee ORM (SQLite/MySQL/PostgreSQL)
│   ├── lora_receiver.py     # 백그라운드 LoRa 수신 스레드
│   ├── web_app.py           # FastAPI + WebSocket
│   ├── api_routes.py        # REST API
│   └── static/
│       ├── index.html       # 웹 대시보드 SPA
│       ├── app.js           # Plotly 차트 + WebSocket 클라이언트
│       └── style.css        # 다크 테마
│
│  ── 실행/빌드 스크립트 ─────────────────
├── setup.bat                # 가상환경 생성 + 기본 의존성 설치
├── run_gui.bat              # 송수신 GUI 실행
├── run_sender.bat           # 송신기 실행
├── run_receiver.bat         # 수신기 실행
├── run_monitor.bat          # 양방향 모니터 실행
├── run_server_gui.bat       # 수신 서버 GUI 실행
├── run_receiver_server.bat  # 수신 서버 CLI 실행
├── run_auto_sender.bat      # 자동 송신기 실행
└── build_server.bat         # PyInstaller exe 빌드
```

---

## 시작하기

### 1. 기본 도구 (송수신)

```bash
setup.bat                     # 최초 1회: 가상환경 + pyserial 설치
run_gui.bat                   # GUI 송수신 도구 실행
```

### 2. 수신 서버 + 웹 대시보드

```bash
pip install -r requirements-server.txt    # 서버 의존성 설치

# GUI로 실행 (권장)
python server_gui.py

# 또는 CLI로 실행
python receiver_server.py --lora-port COM4
python receiver_server.py --no-lora       # LoRa 없이 웹서버만
```

서버 시작 후 브라우저에서 **http://localhost:8080** 접속

### 3. exe 빌드

```bash
build_server.bat
# → dist/lora_server.exe           (GUI 서버 - 더블클릭 실행)
# → dist/lora_receiver_server.exe  (CLI 서버)
# → dist/lora_auto_sender.exe      (자동 송신기)
```

---

## 수신 서버 GUI

`server_gui.py` — 더블클릭으로 실행, 서버 ON/OFF 제어

| 기능 | 설명 |
|---|---|
| **서버 시작/중지** | 버튼 하나로 DB + LoRa 수신 + 웹서버 전체 ON/OFF |
| **COM 포트 선택** | 드롭다운에서 LoRa 장치 선택 |
| **웹 포트 설정** | 대시보드 포트 번호 지정 (기본 8080) |
| **대시보드 열기** | 브라우저에서 실시간 대시보드 바로 열기 |
| **실시간 통계** | 총 수신, 오늘 수신, 분당 수신률, LoRa 상태 |
| **서버 로그** | 모든 동작 로그 실시간 표시 |
| **LoRa 없이 모드** | 체크하면 웹서버만 실행 (테스트용) |

## 웹 대시보드

`http://localhost:8080` — 실시간 수신 모니터링

| 구성 요소 | 설명 |
|---|---|
| 통계 카드 4개 | 총 메시지, 오늘 수신, 분당 수신률, 최근 수신 시각 |
| Plotly 차트 | 시간별 수신량 + 데이터 크기 그래프 |
| 실시간 테이블 | 타임스탬프, 크기, HEX 데이터, 디코딩 텍스트 |
| WebSocket | 새 데이터 즉시 반영 (새로고침 불필요) |

## REST API

| 엔드포인트 | 설명 |
|---|---|
| `GET /api/stats` | 통계 (총 수신, 오늘, 분당 수신률) |
| `GET /api/messages?limit=50` | 최근 수신 메시지 목록 |
| `GET /api/hourly?hours=24` | 시간대별 수신 통계 |
| `GET /docs` | Swagger API 문서 |

---

## 설정 (config.yaml)

```yaml
lora:
  port: "COM4"              # LoRa 시리얼 포트
  baud_rate: 115200
  mode: "stream"            # stream | packet
  configure: false          # true 시 아래 파라미터 적용
  spreading_factor: 7
  channel: 18

database:
  type: "sqlite"            # sqlite | mysql | postgresql
  sqlite_path: "lora_data.db"

web:
  host: "0.0.0.0"
  port: 8080
```

---

## 시스템 아키텍처

```
[센서장비] --serial--> [auto_sender.py] --LoRa TX--> 공중파
                                                       |
[웹 브라우저] <--WebSocket-- [server_gui.py] <--LoRa RX--+
                                  |
                             [SQLite DB]
```

- **server_gui.py**: tkinter GUI (메인 스레드) + uvicorn (서버 스레드) + LoRa 수신 (데몬 스레드)
- 수신 데이터 → DB 저장 → WebSocket 브로드캐스트 → 대시보드 실시간 반영

---

## 기본 도구 CLI 사용법

```bash
# 스트림 모드 수신
python receiver.py --port COM4

# 스트림 모드 송신
python sender.py --port COM3 --message "Hello LoRa!"

# 대화형 송신
python sender.py --port COM3 --interactive

# 패킷 모드 전송
python sender.py --port COM3 --mode packet --target-addr 65534 --target-ch 18 --data AABBCC

# 양방향 모니터
python monitor.py --port COM3

# 반복 전송 (5번, 2초 간격)
python sender.py --port COM3 --message "Test" --repeat 5 --interval 2

# 수신 + 로그 저장
python receiver.py --port COM4 --log received.log
```

## 송신/수신 구분

| 표시 | 의미 | 설명 |
|---|---|---|
| `TX →` | **송신 (Transmit)** | 내가 상대방에게 보낸 데이터 |
| `RX ←` | **수신 (Receive)** | 상대방이 나에게 보낸 데이터 |

## AT 명령어 매개변수

| 매개변수 | AT 명령 | 범위 | 기본값 |
|---|---|---|---|
| 확산 인자 (SF) | `AT+SF=` | 7~12 | 7 |
| 대역폭 (BW) | `AT+BW=` | 0(125K), 1(250K), 2(500K) | 0 |
| 코딩률 (CR) | `AT+CR=` | 1(4/5)~4(4/8) | 1 |
| RF 출력 | `AT+PWR=` | 10~22 dBm | 22 |
| 네트워크 ID | `AT+NETID=` | 0~65535 | 0 |
| 장치 주소 | `AT+ADDR=` | 0~65535 | 0 |
| 송신 채널 | `AT+TXCH=` | 0~80 | 18 |
| 수신 채널 | `AT+RXCH=` | 0~80 | 18 |
| 동작 모드 | `AT+MODE=` | 1(스트림), 2(패킷), 3(릴레이) | 1 |
| RSSI 출력 | `AT+RSSI=` | 0(비활성), 1(활성) | 0 |
| LBT | `AT+LBT=` | 0(비활성), 1(활성) | 0 |

## 참고

- **제품 위키**: https://www.waveshare.com/wiki/USB-TO-LoRa-xF
- 두 장치의 **주소**, **채널**, **SF**, **BW**, **CR** 설정이 동일해야 통신됩니다.
- 주소 `65535` (0xFFFF)는 **브로드캐스트** 모니터링 주소입니다.
