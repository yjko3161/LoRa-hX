# USB-TO-LoRa-xF Python 통신 도구

Waveshare **USB-TO-LoRa-xF** (SX1262) 기반 LoRa 송수신 Python 스크립트입니다.

## 🚀 시작하기 (3단계)

### 1단계: 가상환경 설정
```
setup.bat 실행 (더블클릭)
```

### 2단계: 수신기 실행 (터미널 1)
```
run_receiver.bat 실행
```

### 3단계: 송신기 실행 (터미널 2)
```
run_sender.bat 실행
```

또는 **양방향 모니터** 사용 (하나의 창에서 송수신 동시):
```
run_monitor.bat 실행
```

## 📡 송신 vs 📥 수신 구분

| 표시 | 의미 | 설명 |
|---|---|---|
| `📡 TX →` | **송신 (Transmit)** | 내가 상대방에게 보낸 데이터 |
| `📥 RX ←` | **수신 (Receive)** | 상대방이 나에게 보낸 데이터 |

- `sender.py` = 📡 **송신 전용** (데이터를 보내는 쪽)
- `receiver.py` = 📥 **수신 전용** (데이터를 받는 쪽)
- `monitor.py` = 📡📥 **양방향** (하나의 창에서 송신+수신 동시)

## 배치 파일 안내

| 파일 | 설명 |
|---|---|
| `setup.bat` | 가상환경 생성 + pyserial 설치 (**최초 1회**) |
| `run_sender.bat` | 📡 송신기 실행 (COM 포트 자동 탐색) |
| `run_receiver.bat` | 📥 수신기 실행 (로그 저장 옵션) |
| `run_monitor.bat` | 📡📥 양방향 모니터 (송수신 동시) |

## 파이썬 모듈

| 파일 | 설명 |
|---|---|
| `lora_config.py` | AT 명령어 설정 모듈 (LoRaConfig, LoRaParams) |
| `sender.py` | 송신기 (스트림/패킷 모드, CLI 지원) |
| `receiver.py` | 수신기 (스트림/패킷 모드, 로그 지원) |
| `monitor.py` | 양방향 모니터 (송수신 동시) |
| `examples.py` | 다양한 사용 예제 |

## CLI 사용법

```bash
# 스트림 모드 수신
python receiver.py --port COM4

# 스트림 모드 송신 (단일 메시지)
python sender.py --port COM3 --message "Hello LoRa!"

# 대화형 송신
python sender.py --port COM3 --interactive

# 패킷 모드 (주소 지정 전송)
python sender.py --port COM3 --mode packet --target-addr 65534 --target-ch 18 --data AABBCC

# 양방향 모니터
python monitor.py --port COM3

# 반복 전송 (5번, 2초 간격)
python sender.py --port COM3 --message "Test" --repeat 5 --interval 2

# 수신 + 로그 저장
python receiver.py --port COM4 --log received.log
```

## AT 명령어 매개변수 표

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
