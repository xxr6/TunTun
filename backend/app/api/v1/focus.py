"""专注接口：记录番茄钟会话 + 时长汇总。"""
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.focus import FocusSession
from app.models.user import User
from app.schemas.focus import FocusSessionCreate, FocusSessionOut, FocusSummary

router = APIRouter(prefix="/focus", tags=["focus"])


@router.post("/sessions", response_model=FocusSessionOut, status_code=201)
async def create_session(
    body: FocusSessionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    s = FocusSession(
        user_id=user.id,
        mode=body.mode,
        started_at=body.started_at,
        ended_at=body.ended_at,
        duration_seconds=body.duration_seconds,
        completed=body.completed,
        deck_id=body.deck_id,
        deck_name=body.deck_name,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return FocusSessionOut.model_validate(s)


@router.get("/sessions", response_model=list[FocusSessionOut])
async def list_sessions(
    limit: int = 20, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    sessions = (
        await db.scalars(
            select(FocusSession)
            .where(FocusSession.user_id == user.id)
            .order_by(FocusSession.started_at.desc())
            .limit(limit)
        )
    ).all()
    return [FocusSessionOut.model_validate(s) for s in sessions]


@router.get("/summary", response_model=FocusSummary)
async def summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 用户本地时区：本地零点 / 周一零点 / 月初零点（保持 aware datetime）
    tz = ZoneInfo(user.timezone or "Asia/Shanghai")
    now_local = datetime.now(tz)
    day_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start_local = day_start_local - timedelta(days=now_local.weekday())
    month_start_local = day_start_local.replace(day=1)
    # 库中时间统一存 UTC，查询比较时换算成 UTC aware 时刻
    day_start = day_start_local.astimezone(timezone.utc)
    week_start = week_start_local.astimezone(timezone.utc)
    month_start = month_start_local.astimezone(timezone.utc)

    # 分段统计：只计 completed=True 且 mode != "nap" 的会话
    rows = (
        await db.execute(
            select(FocusSession.started_at, FocusSession.duration_seconds).where(
                FocusSession.user_id == user.id,
                FocusSession.completed == True,
                FocusSession.mode != "nap",
                FocusSession.started_at >= month_start,
            )
        )
    ).all()

    today = week = month = 0
    today_count = 0
    for started_at, dur in rows:
        month += dur
        if started_at >= week_start:
            week += dur
        if started_at >= day_start:
            today += dur
            today_count += 1

    return FocusSummary(
        today_seconds=today, week_seconds=week, month_seconds=month, today_count=today_count
    )
