"""专注会话模型。"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UTCDateTime, uuid_pk

# 专注模式：pomodoro 啃25 / deep 深啃50 / nap 打盹5 / custom 自定义
FOCUS_MODES = ("pomodoro", "deep", "nap", "custom")


class FocusSession(Base, TimestampMixin):
    __tablename__ = "focus_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    mode: Mapped[str] = mapped_column(String(16), default="pomodoro", nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    ended_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    # 番茄钟是否完整走完（未走完也可记录，completed=False 表示中途放弃）
    completed: Mapped[bool] = mapped_column(default=True, nullable=False)
    # 「这一轮啃什么」的卡组快照：记录会话当时的卡组 id 与名称，允许为空
    deck_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    deck_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
