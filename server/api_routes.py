"""
REST API 라우트
/api/messages, /api/stats, /api/hourly 등
"""

from datetime import datetime

from fastapi import APIRouter, Query

from server.database import DatabaseManager

router = APIRouter(prefix="/api")

# 런타임에 set_db_manager()로 주입
_db: DatabaseManager = None


def set_db_manager(db_manager: DatabaseManager):
    global _db
    _db = db_manager


@router.get("/messages")
def get_messages(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    """최근 수신 메시지 목록"""
    messages = _db.get_recent_messages(limit=limit, offset=offset)
    return [
        {
            "id": msg.id,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_hex": msg.raw_hex,
            "decoded_text": msg.decoded_text,
            "byte_length": msg.byte_length,
            "source_info": msg.source_info,
        }
        for msg in messages
    ]


@router.get("/stats")
def get_stats():
    """대시보드 통계"""
    last_time = _db.get_last_received_time()
    return {
        "total_count": _db.get_total_count(),
        "today_count": _db.get_today_count(),
        "messages_per_minute": round(_db.get_messages_per_minute(minutes=5), 2),
        "last_received": last_time.strftime("%Y-%m-%d %H:%M:%S") if last_time else None,
    }


@router.get("/hourly")
def get_hourly(hours: int = Query(24, ge=1, le=168)):
    """시간대별 수신 통계"""
    hourly = _db.get_hourly_stats(hours=hours)
    labels = sorted(hourly.keys())
    return {
        "labels": labels,
        "counts": [hourly[k]["count"] for k in labels],
        "bytes": [hourly[k]["total_bytes"] for k in labels],
    }
