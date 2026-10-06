"""AI 提炼相关输入输出模型。"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExtractFromFileIn(BaseModel):
    document_id: uuid.UUID


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_type: str
    front: str
    back: str
    confidence: float
    card_id: uuid.UUID | None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content_md: str
    source_file_id: uuid.UUID | None
    source_type: str
    status: str
    created_at: datetime


class NoteDetailOut(NoteOut):
    candidates: list[CandidateOut] = []


class SplitCandidatesIn(BaseModel):
    candidate_ids: list[uuid.UUID] = Field(min_length=1)
    deck_id: uuid.UUID
