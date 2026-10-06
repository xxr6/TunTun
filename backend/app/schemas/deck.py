"""卡组输入输出模型。"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeckCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_id: uuid.UUID | None = None
    description: str = ""
    config: dict[str, Any] = {}


class DeckUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    config: dict[str, Any] | None = None


class DeckMove(BaseModel):
    parent_id: uuid.UUID | None = None


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    description: str
    config: dict[str, Any]
    position: int
    card_count: int = 0
    created_at: datetime
