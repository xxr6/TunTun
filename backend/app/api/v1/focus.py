"""专注接口：记录番茄钟会话 + 时长汇总。"""
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import conflict
from app.models.focus import FocusSession
from app.models.user import User
from app.schemas.focus import FocusSessionCreate, FocusSessionOut, FocusSummary

router = APIRouter(prefix="/focus", tags=["focus"])


@router.post("/sessions", response_model=FocusSessionOut, status_code=201)
async def create_session(
    body: FocusSessionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    if body.id is not None:
        existing = await db.get(FocusSession, body.id)
        if existing is not None:
            if existing.user_id != user.id:
                raise conflict("专注记录 ID 已被使用")
            return FocusSessionOut.model_validate(existing)
    s = FocusSession(
        **({"id": body.id} if body.id is not None else {}),
        user_id=user.id,
        mode=body.mode,
        started_at=body.started_at,
        ended_at=body.ended_at,
        duration_seconds=body.duration_seconds,
        completed=body.completed,
        interrupted=body.interrupted,
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

    # 完成和主动打断的时长都计入；重置不计入，打盹不计入
    rows = (
        await db.execute(
            select(FocusSession.started_at, FocusSession.duration_seconds, FocusSession.completed, FocusSession.mode).where(
                FocusSession.user_id == user.id,
                or_(FocusSession.completed.is_(True), FocusSession.interrupted.is_(True)),
                FocusSession.mode != "nap",
                FocusSession.started_at >= month_start,
            )
        )
    ).all()

    today = week = month = 0
    today_count = 0
    for started_at, dur, completed, mode in rows:
        month += dur
        if started_at >= week_start:
            week += dur
        if started_at >= day_start:
            today += dur
            if completed and mode == "pomodoro":
                today_count += 1

    return FocusSummary(
        today_seconds=today, week_seconds=week, month_seconds=month, today_count=today_count
    )
