"""复习相关输入输出模型。"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewAnswer(BaseModel):
    card_id: uuid.UUID
    rating: int = Field(ge=1, le=4)
    duration_ms: int | None = None
    reviewed_at: datetime | None = None


class ReviewAnswerOut(BaseModel):
    card_id: uuid.UUID
    state: str
    due: datetime
    stability: float | None
    difficulty: float | None
    scheduled_days: float
    remaining_today: int


class ReviewCard(BaseModel):
    """复习队列返回的单张卡片（含正面背面，供翻卡）。"""
    card_id: uuid.UUID
    deck_id: uuid.UUID
    deck_name: str
    card_type: str
    front: str
    back: str
    hint: str | None
    tags: list[str]
    state: str
    reps: int
    due: datetime


class ReviewQueueOut(BaseModel):
    items: list[ReviewCard]
    remaining_today: int


class ReviewUndoOut(BaseModel):
    undone: bool
    card_id: uuid.UUID
