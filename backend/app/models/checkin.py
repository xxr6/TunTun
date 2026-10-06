"""每日签到模型。"""
import uuid

from sqlalchemy import String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class DailyCheckin(Base, TimestampMixin):
    __tablename__ = "daily_checkins"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_checkin_user_day"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    # 签到日期，存 "YYYY-MM-DD"（按用户时区）
    day: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
