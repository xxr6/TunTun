"""每日签到接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.checkin import DailyCheckin
from app.models.user import User
from app.schemas.checkin import CheckinOut
from app.services.checkin import checkin_achievements, checkin_summary, today_str

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.get("", response_model=CheckinOut)
async def get_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = today_str(user.timezone)
    checked = (
        await db.scalar(
            select(DailyCheckin.id).where(
                DailyCheckin.user_id == user.id, DailyCheckin.day == today
            )
        )
        is not None
    )
    s = await checkin_summary(db, user.id, user.timezone)
    return CheckinOut(
        checked=checked, streak=s["streak"], total_days=s["total_days"],
        month_days=s["month_days"], new_achievements=[],
    )


@router.post("", response_model=CheckinOut)
async def do_checkin(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = today_str(user.timezone)
    exists = await db.scalar(
        select(DailyCheckin.id).where(DailyCheckin.user_id == user.id, DailyCheckin.day == today)
    )
    before = await checkin_summary(db, user.id, user.timezone)
    new_names: list[str] = []
    if exists is None:
        db.add(DailyCheckin(user_id=user.id, day=today))
        await db.commit()
        after = await checkin_summary(db, user.id, user.timezone)
        before_unlocked = {a["name"] for a in checkin_achievements(**before) if a["unlocked"]}
        after_unlocked = {a["name"] for a in checkin_achievements(**after) if a["unlocked"]}
        new_names = sorted(after_unlocked - before_unlocked)
    else:
        after = before
    return CheckinOut(
        checked=True, streak=after["streak"], total_days=after["total_days"],
        month_days=after["month_days"], new_achievements=new_names,
    )
