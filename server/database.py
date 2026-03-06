"""
Peewee ORM 데이터베이스 모듈
LoRa 수신 메시지 저장 및 조회
"""

import os
from datetime import datetime, timedelta

from peewee import (
    Model, AutoField, DateTimeField, BlobField, CharField,
    TextField, IntegerField, SqliteDatabase, MySQLDatabase,
    PostgresqlDatabase, DatabaseProxy,
)

# 프록시 — 런타임에 실제 DB 바인딩
database_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class LoRaMessage(BaseModel):
    """LoRa 수신 메시지 테이블"""

    class Meta:
        table_name = "lora_messages"

    id = AutoField()
    timestamp = DateTimeField(index=True, default=datetime.now)
    raw_bytes = BlobField()
    raw_hex = CharField(max_length=2048)
    decoded_text = TextField(null=True)
    byte_length = IntegerField()
    source_info = CharField(max_length=255, null=True)


class DatabaseManager:
    """DB 초기화, 메시지 저장/조회 관리"""

    def __init__(self, config: dict):
        self.config = config
        self.db = None

    def initialize(self):
        """설정에 따라 DB 연결 및 테이블 생성"""
        db_type = self.config.get("type", "sqlite")

        if db_type == "sqlite":
            db_path = self.config.get("sqlite_path", "lora_data.db")
            self.db = SqliteDatabase(db_path, pragmas={
                "journal_mode": "wal",
                "cache_size": -1024 * 64,
                "foreign_keys": 1,
            })
            print(f"[DB] SQLite: {os.path.abspath(db_path)}")

        elif db_type == "mysql":
            self.db = MySQLDatabase(
                self.config["name"],
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
            )
            print(f"[DB] MySQL: {self.config['host']}:{self.config['port']}/{self.config['name']}")

        elif db_type == "postgresql":
            self.db = PostgresqlDatabase(
                self.config["name"],
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                user=self.config.get("user", "postgres"),
                password=self.config.get("password", ""),
            )
            print(f"[DB] PostgreSQL: {self.config['host']}:{self.config['port']}/{self.config['name']}")

        else:
            raise ValueError(f"지원하지 않는 DB 타입: {db_type}")

        # 프록시 바인딩
        database_proxy.initialize(self.db)
        self.db.connect()
        self.db.create_tables([LoRaMessage])
        print("[DB] 테이블 준비 완료")

    def close(self):
        if self.db and not self.db.is_closed():
            self.db.close()

    # ── 저장 ──────────────────────────────────────────────

    def save_message(self, raw_data: bytes, source_info: str = None) -> LoRaMessage:
        """수신 데이터를 DB에 저장"""
        raw_hex = " ".join(f"{b:02X}" for b in raw_data)
        try:
            decoded_text = raw_data.decode("utf-8", errors="replace")
        except Exception:
            decoded_text = None

        msg = LoRaMessage.create(
            timestamp=datetime.now(),
            raw_bytes=raw_data,
            raw_hex=raw_hex,
            decoded_text=decoded_text,
            byte_length=len(raw_data),
            source_info=source_info,
        )
        return msg

    # ── 조회 ──────────────────────────────────────────────

    def get_recent_messages(self, limit: int = 50, offset: int = 0):
        """최근 메시지 조회 (최신순)"""
        return (
            LoRaMessage
            .select()
            .order_by(LoRaMessage.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

    def get_total_count(self) -> int:
        return LoRaMessage.select().count()

    def get_today_count(self) -> int:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return LoRaMessage.select().where(LoRaMessage.timestamp >= today_start).count()

    def get_messages_per_minute(self, minutes: int = 1) -> float:
        """최근 N분간 분당 수신률"""
        since = datetime.now() - timedelta(minutes=minutes)
        count = LoRaMessage.select().where(LoRaMessage.timestamp >= since).count()
        return count / max(minutes, 1)

    def get_last_received_time(self):
        """마지막 수신 시각"""
        msg = LoRaMessage.select().order_by(LoRaMessage.timestamp.desc()).first()
        if msg:
            return msg.timestamp
        return None

    def get_hourly_stats(self, hours: int = 24):
        """시간대별 수신 통계 (최근 N시간)"""
        since = datetime.now() - timedelta(hours=hours)
        messages = (
            LoRaMessage
            .select()
            .where(LoRaMessage.timestamp >= since)
            .order_by(LoRaMessage.timestamp)
        )

        hourly = {}
        for msg in messages:
            hour_key = msg.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in hourly:
                hourly[hour_key] = {"count": 0, "total_bytes": 0}
            hourly[hour_key]["count"] += 1
            hourly[hour_key]["total_bytes"] += msg.byte_length

        return hourly
