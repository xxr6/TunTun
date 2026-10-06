"""AI 提炼笔记与考点候选模型。"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk

# 提炼来源类型
SOURCE_TYPES = ("file", "video", "url")


class Note(Base, TimestampMixin):
    """AI 提炼产物：一份可下载、可编辑、可拆卡的 Markdown 笔记。"""
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    source_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="file", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, default="", nullable=False)
    outline: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="done", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class NoteCandidate(Base):
    """笔记里可拆成卡片的考点候选。"""
    __tablename__ = "note_candidates"

    id: Mapped[uuid.UUID] = uuid_pk()
    note_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    card_type: Mapped[str] = mapped_column(String(16), default="basic", nullable=False)
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    # 拆卡后关联生成的卡片
    card_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
