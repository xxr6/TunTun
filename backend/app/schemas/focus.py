"""专注会话输入输出模型。"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class FocusSessionCreate(BaseModel):
    id: uuid.UUID | None = None  # 客户端重试时沿用同一 ID，避免重复计时
    mode: Literal["pomodoro", "deep", "nap", "custom", "countup"] = "pomodoro"
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    completed: bool = True
    interrupted: bool = False
    deck_id: uuid.UUID | None = None
    deck_name: str = ""


class FocusSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mode: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    completed: bool
    interrupted: bool
    deck_id: uuid.UUID | None
    deck_name: str


class FocusSummary(BaseModel):
    today_seconds: int
    week_seconds: int
    month_seconds: int
    today_count: int
