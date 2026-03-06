@echo off
chcp 65001 >nul
echo ============================================================
echo  LoRa-hX 수신 서버 빌드 (PyInstaller)
echo ============================================================
echo.

:: 의존성 확인
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller 설치 중...
    python -m pip install pyinstaller
)

:: 이전 빌드 정리
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: GUI 서버 빌드 (메인)
echo [1/3] lora_server.exe 빌드 중... (GUI)
python -m PyInstaller --onefile --windowed --name lora_server ^
    --add-data "config.yaml;." ^
    --add-data "server/static;server/static" ^
    --add-data "lora_config.py;." ^
    --hidden-import lora_config ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.http.h11_impl ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.protocols.websockets.wsproto_impl ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import uvicorn.lifespan.off ^
    --hidden-import uvicorn.protocols.websockets.websockets_impl ^
    server_gui.py

if errorlevel 1 (
    echo [오류] GUI 서버 빌드 실패
    pause
    exit /b 1
)

:: CLI 수신 서버 빌드
echo [2/3] lora_receiver_server.exe 빌드 중... (CLI)
python -m PyInstaller --onefile --name lora_receiver_server ^
    --add-data "config.yaml;." ^
    --add-data "server/static;server/static" ^
    --add-data "lora_config.py;." ^
    --hidden-import lora_config ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.http.h11_impl ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.protocols.websockets.wsproto_impl ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import uvicorn.lifespan.off ^
    --hidden-import uvicorn.protocols.websockets.websockets_impl ^
    receiver_server.py

if errorlevel 1 (
    echo [오류] CLI 서버 빌드 실패
    pause
    exit /b 1
)

:: 자동 송신기 빌드
echo [3/3] lora_auto_sender.exe 빌드 중...
python -m PyInstaller --onefile --name lora_auto_sender ^
    --add-data "config.yaml;." ^
    --add-data "lora_config.py;." ^
    --hidden-import lora_config ^
    auto_sender.py

if errorlevel 1 (
    echo [오류] 자동 송신기 빌드 실패
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  빌드 완료!
echo  dist\lora_server.exe          (GUI - 더블클릭 실행)
echo  dist\lora_receiver_server.exe (CLI)
echo  dist\lora_auto_sender.exe     (자동 송신기)
echo ============================================================
echo.
echo [참고] 실행 시 같은 폴더에 config.yaml을 복사하세요.
pause
