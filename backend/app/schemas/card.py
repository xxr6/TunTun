"""卡片输入输出模型。"""
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.card_quality import card_quality_error

CardType = Literal["basic", "cloze", "quote", "image"]
CardState = Literal["new", "learning", "review", "relearning", "suspended", "buried"]


class CardCreate(BaseModel):
    # deck_id 可选：为空时落到用户的默认卡组「收件箱」（不存在则自动创建），
    # 阅读器划词成卡时可以不带卡组直接入库。
    deck_id: uuid.UUID | None = None
    card_type: CardType = "basic"
    front: str = Field(min_length=1)
    back: str = ""
    hint: str | None = None
    extra: dict[str, Any] = {}
    source_file_id: uuid.UUID | None = None
    source_locator: dict[str, Any] | None = None
    tags: list[str] = []

    @model_validator(mode="after")
    def validate_study_card(self):
        error = card_quality_error(self.card_type, self.front, self.back)
        if error:
            raise ValueError(error)
        return self


class CardUpdate(BaseModel):
    card_type: CardType | None = None
    front: str | None = None
    back: str | None = None
    hint: str | None = None
    extra: dict[str, Any] | None = None
    tags: list[str] | None = None
    state: CardState | None = None  # 允许挂起/恢复/挖出


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    deck_id: uuid.UUID
    card_type: str
    front: str
    back: str
    hint: str | None
    extra: dict[str, Any]
    source_file_id: uuid.UUID | None
    source_locator: dict[str, Any] | None
    tags: list[str]
    state: str
    due: datetime
    created_at: datetime


class CardBulkAction(BaseModel):
    card_ids: list[uuid.UUID]
    deck_id: uuid.UUID | None = None
    tags_add: list[str] | None = None
    tags_remove: list[str] | None = None
    action: Literal["move", "tag", "suspend", "unsuspend", "delete"] = "move"


class CardListOut(BaseModel):
    items: list[CardOut]
    total: int
