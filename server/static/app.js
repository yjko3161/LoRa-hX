/**
 * LoRa-hX Dashboard — Plotly 차트 + WebSocket 클라이언트
 */

// ── 상태 ────────────────────────────────────
let ws = null;
let reconnectTimer = null;
const MAX_TABLE_ROWS = 200;

// ── 초기화 ──────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadStats();
    loadMessages();
    loadHourlyChart();
    connectWebSocket();

    // 주기적 갱신 (30초)
    setInterval(loadStats, 30000);
    setInterval(loadHourlyChart, 60000);
});

// ── REST API 호출 ───────────────────────────
async function loadStats() {
    try {
        const res = await fetch("/api/stats");
        const data = await res.json();
        document.getElementById("stat-total").textContent = data.total_count.toLocaleString();
        document.getElementById("stat-today").textContent = data.today_count.toLocaleString();
        document.getElementById("stat-rate").textContent = data.messages_per_minute;
        document.getElementById("stat-last").textContent = data.last_received || "-";
    } catch (e) {
        console.error("Stats load error:", e);
    }
}

async function loadMessages() {
    try {
        const res = await fetch("/api/messages?limit=100");
        const messages = await res.json();
        const tbody = document.getElementById("message-tbody");
        if (messages.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-row">수신된 데이터가 없습니다</td></tr>';
            return;
        }
        tbody.innerHTML = messages.map(msg => messageRow(msg)).join("");
    } catch (e) {
        console.error("Messages load error:", e);
    }
}

async function loadHourlyChart() {
    try {
        const res = await fetch("/api/hourly?hours=24");
        const data = await res.json();
        renderChart(data);
    } catch (e) {
        console.error("Hourly chart error:", e);
    }
}

// ── 테이블 행 생성 ──────────────────────────
function messageRow(msg, isNew) {
    const cls = isNew ? ' class="new-row"' : "";
    const hex = escapeHtml(msg.raw_hex || "");
    const text = escapeHtml(msg.decoded_text || "");
    return `<tr${cls}>
        <td>${msg.id}</td>
        <td>${msg.timestamp}</td>
        <td>${msg.byte_length}B</td>
        <td title="${hex}">${hex}</td>
        <td title="${text}">${text}</td>
    </tr>`;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ── Plotly 차트 ─────────────────────────────
function renderChart(data) {
    const countTrace = {
        x: data.labels,
        y: data.counts,
        type: "bar",
        name: "수신 건수",
        marker: { color: "#00d4ff", opacity: 0.8 },
        yaxis: "y",
    };

    const bytesTrace = {
        x: data.labels,
        y: data.bytes,
        type: "scatter",
        mode: "lines+markers",
        name: "데이터 크기 (bytes)",
        line: { color: "#ff6b6b", width: 2 },
        marker: { size: 5 },
        yaxis: "y2",
    };

    const layout = {
        paper_bgcolor: "#16213e",
        plot_bgcolor: "#0a0a1a",
        font: { color: "#e0e0e0", size: 12 },
        margin: { l: 55, r: 55, t: 10, b: 50 },
        xaxis: {
            gridcolor: "#2a2a4a",
            tickangle: -45,
        },
        yaxis: {
            title: "건수",
            gridcolor: "#2a2a4a",
            side: "left",
        },
        yaxis2: {
            title: "bytes",
            overlaying: "y",
            side: "right",
            gridcolor: "transparent",
        },
        legend: {
            orientation: "h",
            y: 1.12,
            x: 0.5,
            xanchor: "center",
        },
        bargap: 0.3,
    };

    Plotly.newPlot("hourly-chart", [countTrace, bytesTrace], layout, {
        responsive: true,
        displayModeBar: false,
    });
}

// ── WebSocket ───────────────────────────────
function connectWebSocket() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${location.host}/ws`;

    ws = new WebSocket(url);

    ws.onopen = () => {
        setWsStatus(true);
        if (reconnectTimer) {
            clearInterval(reconnectTimer);
            reconnectTimer = null;
        }
    };

    ws.onclose = () => {
        setWsStatus(false);
        scheduleReconnect();
    };

    ws.onerror = () => {
        setWsStatus(false);
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === "new_message") {
                onNewMessage(msg.data);
            }
        } catch (e) {
            console.error("WS message parse error:", e);
        }
    };
}

function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setInterval(() => {
        if (!ws || ws.readyState === WebSocket.CLOSED) {
            connectWebSocket();
        }
    }, 3000);
}

function setWsStatus(connected) {
    const dot = document.getElementById("ws-status");
    const text = document.getElementById("ws-status-text");
    if (connected) {
        dot.className = "status-dot connected";
        text.textContent = "실시간 연결됨";
    } else {
        dot.className = "status-dot disconnected";
        text.textContent = "연결 끊김 — 재연결 중...";
    }
}

// ── 새 메시지 실시간 처리 ───────────────────
function onNewMessage(data) {
    // 통계 갱신
    loadStats();

    // 테이블 상단에 삽입
    const tbody = document.getElementById("message-tbody");
    const emptyRow = tbody.querySelector(".empty-row");
    if (emptyRow) {
        emptyRow.parentElement.remove();
    }

    const temp = document.createElement("tbody");
    temp.innerHTML = messageRow(data, true);
    const newRow = temp.firstElementChild;
    tbody.insertBefore(newRow, tbody.firstChild);

    // 최대 행 수 제한
    while (tbody.children.length > MAX_TABLE_ROWS) {
        tbody.removeChild(tbody.lastChild);
    }
}
