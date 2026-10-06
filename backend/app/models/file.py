"""文件、文档、分块模型。"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UTCDateTime, uuid_pk

# 文档解析状态机
DOC_STATUSES = ("queued", "parsing", "done", "failed")


class File(Base, TimestampMixin):
    """文件 / 文件夹（目录树）。文件夹 is_dir=True，无 storage_path 与 hash。"""
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_dir: Mapped[bool] = mapped_column(default=False, nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    ext: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), default="", index=True, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)  # 软删进回收站


class Document(Base, TimestampMixin):
    """文件的解析产物：纯文本正文 + 状态。"""
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Chunk(Base, TimestampMixin):
    """文档分块（RAG 检索最小单位，M5 用）。M3 先建表，暂不填充。"""
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    locator: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
