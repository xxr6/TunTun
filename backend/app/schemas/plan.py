"""今日计划输入输出模型。"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    day: str | None = None


class PlanUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    day: str
    title: str
    done: bool
    created_at: datetime
