"""用户输出模型。"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    timezone: str
    settings: dict[str, Any]
    created_at: datetime


class UserUpdate(BaseModel):
    timezone: str | None = None
