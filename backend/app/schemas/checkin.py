"""签到输出模型。"""
from pydantic import BaseModel


class CheckinOut(BaseModel):
    checked: bool
    streak: int
    total_days: int
    month_days: int
    new_achievements: list[str] = []
