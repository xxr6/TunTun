"""卡片、FSRS 调度状态、复习记录模型。"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UTCDateTime, uuid_pk

# 卡片状态机（业务状态）。new/learning/review/relearning 参与调度，suspended/buried 挂起。
CARD_STATES = ("new", "learning", "review", "relearning", "suspended", "buried")
CARD_TYPES = ("basic", "cloze", "quote", "image")


class Card(Base, TimestampMixin):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = uuid_pk()
    deck_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("decks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # 冗余 user_id，所有查询强制按它过滤（权限隔离，见技术文档 17 章）
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    card_type: Mapped[str] = mapped_column(String(16), default="basic", nullable=False)
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, default="", nullable=False)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 扩展字段：例句、词根、近义词等
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # 溯源：来自哪个文件、哪个位置
    source_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    source_locator: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)  # 跨方言用 JSON 存数组

    state: Mapped[str] = mapped_column(String(16), default="new", index=True, nullable=False)
    due: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    state_info: Mapped["CardState | None"] = relationship(
        back_populates="card", cascade="all, delete-orphan", uselist=False
    )


class CardState(Base):
    """FSRS 调度状态，与 cards 一对一。"""
    __tablename__ = "card_states"

    card_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True
    )
    stability: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    # fsrs 6.x 的学习步骤索引（Learning 状态推进依赖它，必须持久化；转 Review 后为 None）
    step: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_review: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    elapsed_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    scheduled_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    fsrs_params: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    card: Mapped["Card"] = relationship(back_populates="state_info")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    card_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=Again 2=Hard 3=Good 4=Easy
    state_before: Mapped[str] = mapped_column(String(16), nullable=False)
    state_after: Mapped[str] = mapped_column(String(16), nullable=False)
    stability_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    stability_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_before: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    due_after: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    last_review_before: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    elapsed_days: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    scheduled_days: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    review_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
