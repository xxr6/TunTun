"""今日计划模型。"""
import uuid

from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class PlanTask(Base, TimestampMixin):
    __tablename__ = "plan_tasks"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    # 所属日期，存 "YYYY-MM-DD"（按用户时区）
    day: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
