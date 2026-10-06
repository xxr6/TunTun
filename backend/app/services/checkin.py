"""签到统计与成就：供签到接口与统计成就引擎复用。"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import DailyCheckin


def today_str(user_timezone: str) -> str:
    """按用户时区的「今天」，返回 YYYY-MM-DD。"""
    tz = ZoneInfo(user_timezone or "Asia/Shanghai")
    return datetime.now(tz).strftime("%Y-%m-%d")


async def checkin_summary(db: AsyncSession, user_id, user_timezone: str) -> dict:
    """返回 {streak, total_days, month_days}。streak 从今天（若已签）或昨天（若未签今天）向前连续计数。"""
    rows = (
        await db.scalars(
            select(DailyCheckin.day).where(DailyCheckin.user_id == user_id)
        )
    ).all()
    day_set = set(rows)
    days_sorted = sorted(day_set, reverse=True)
    total_days = len(day_set)
    today = today_str(user_timezone)
    month_days = sum(1 for d in day_set if d.startswith(today[:7]))

    streak = 0
    anchor: date | None = None
    if today in day_set:
        anchor = date.fromisoformat(today)
    else:
        yest = (datetime.now(ZoneInfo(user_timezone or "Asia/Shanghai")) - timedelta(days=1)).strftime("%Y-%m-%d")
        if yest in day_set:
            anchor = date.fromisoformat(yest)
    if anchor is not None:
        d = anchor
        while d.isoformat() in day_set:
            streak += 1
            d -= timedelta(days=1)

    return {"streak": streak, "total_days": total_days, "month_days": month_days}


def checkin_achievements(streak: int, total_days: int, month_days: int) -> list[dict]:
    """「签到」组成就，shape 与 stats._achievements 保持一致。"""

    def mk(name, desc, icon, cur, target, rarity):
        return {
            "group": "签到",
            "name": name,
            "desc": desc,
            "icon": icon,
            "progress": min(cur, target),
            "target": target,
            "unlocked": cur >= target,
            "rarity": rarity,
        }

    return [
        mk("初来乍到", "累计签到 1 天", "#i-calendar", total_days, 1, "铜"),
        mk("七日之约", "连续签到 7 天", "#i-star", streak, 7, "银"),
        mk("月满勤", "本月签到 21 天", "#i-target", month_days, 21, "银"),
        mk("百日常客", "累计签到 100 天", "#i-crown", total_days, 100, "金"),
    ]
