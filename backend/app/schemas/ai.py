"""AI 生成相关输入输出模型。"""
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class CardSelectionIn(BaseModel):
    document_id: uuid.UUID
    selection: str = Field(min_length=1)
    locator: dict[str, Any] | None = None
    target_deck_id: uuid.UUID | None = None
    mode: Literal["auto", "basic", "cloze", "quote"] = "auto"
    max_cards: int = Field(default=3, ge=1, le=10)


class GeneratedCard(BaseModel):
    card_type: str
    front: str
    back: str
    hint: str | None = None
    confidence: float = 1.0


class CardSelectionOut(BaseModel):
    cards: list[GeneratedCard]
    fallback: bool = False  # True = 未配置 LLM，走模板化兜底
