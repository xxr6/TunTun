"""文件与文档输出模型。"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    is_dir: bool
    size: int
    mime_type: str
    ext: str
    created_at: datetime
    doc_id: uuid.UUID | None = None
    doc_status: str | None = None  # 关联 Document 的解析状态
    doc_error: str | None = None   # 解析失败原因（status=failed 时有值）
    page_count: int | None = None


class FolderCreate(BaseModel):
    name: str
    parent_id: uuid.UUID | None = None


class FileUpdate(BaseModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_id: uuid.UUID
    title: str
    status: str
    error: str | None
    page_count: int | None
    created_at: datetime


class DocumentContentOut(BaseModel):
    document_id: uuid.UUID
    file_id: uuid.UUID
    title: str
    page_count: int | None
    text: str
