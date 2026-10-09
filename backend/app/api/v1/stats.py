"""统计接口：总览、热力图、统计页 dashboard 聚合。"""
import datetime as _dt
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.ai_usage import AiUsage
from app.models.card import Card, CardState, ReviewLog
from app.models.deck import Deck
from app.models.file import File
from app.models.focus import FocusSession
from app.models.note import Note
from app.models.user import User
from app.services.checkin import checkin_achievements, checkin_summary

router = APIRouter(prefix="/stats", tags=["stats"])


def _counted_focus():
    """完整结束或主动打断的专注时长；重置记录不参与统计。"""
    return or_(FocusSession.completed.is_(True), FocusSession.interrupted.is_(True))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _user_tz(user: User) -> ZoneInfo:
    return ZoneInfo(user.timezone or "Asia/Shanghai")


@router.get("/overview")
async def overview(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 用户本地零点（aware），换算成 UTC 与库中时间比较
    now_local = datetime.now(_user_tz(user))
    day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(
        timezone.utc
    )

    total_cards = await db.scalar(
        select(func.count(Card.id)).where(Card.user_id == user.id, Card.deleted_at.is_(None))
    ) or 0
    total_decks = await db.scalar(
        select(func.count(Deck.id)).where(Deck.user_id == user.id)
    ) or 0
    total_reviews = await db.scalar(
        select(func.count(ReviewLog.id)).where(ReviewLog.user_id == user.id)
    ) or 0
    today_reviews = await db.scalar(
        select(func.count(ReviewLog.id)).where(
            ReviewLog.user_id == user.id, ReviewLog.reviewed_at >= day_start
        )
    ) or 0
    focus_seconds = await db.scalar(
        select(func.coalesce(func.sum(FocusSession.duration_seconds), 0)).where(
            FocusSession.user_id == user.id,
            _counted_focus(),
            FocusSession.mode != "nap",
        )
    ) or 0

    return {
        "total_cards": total_cards,
        "total_decks": total_decks,
        "total_reviews": total_reviews,
        "today_reviews": today_reviews,
        "focus_seconds": focus_seconds,
    }


@router.get("/heatmap")
async def heatmap(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """过去 13 周每天的复习次数，返回 91 个 [date, count]。"""
    tz = _user_tz(user)
    now_local = datetime.now(tz)
    today = now_local.replace(hour=0, minute=0, second=0, microsecond=0)  # 本地今天零点
    start = today - _dt.timedelta(days=90)  # 本地今天 - 90 天（aware）
    start_utc = start.astimezone(timezone.utc)  # 查询用 aware 时刻

    rows = (
        await db.execute(
            select(ReviewLog.reviewed_at).where(
                ReviewLog.user_id == user.id, ReviewLog.reviewed_at >= start_utc
            )
        )
    ).all()

    counts: dict[str, int] = {}
    for (reviewed_at,) in rows:
        # 把 UTC 时间转成用户时区再取日期分桶
        key = reviewed_at.astimezone(tz).date().isoformat()
        counts[key] = counts.get(key, 0) + 1

    result = []
    for i in range(91):
        day = (start + _dt.timedelta(days=i)).date()
        result.append({"date": day.isoformat(), "count": counts.get(day.isoformat(), 0)})
    return result


# ────────────────────────────────────────────────────────────────
# 统计页 dashboard 聚合（专注三卡 / 指标行 / 遗忘曲线 / 卡组健康度 / 成就）
# ────────────────────────────────────────────────────────────────

# 专注目标默认值（秒）——用户可在个人中心改，存 user.settings.focus_goals
FOCUS_GOALS = {"today": 3 * 3600, "week": 20 * 3600, "month": 80 * 3600}


def _user_focus_goals(user) -> dict:
    """settings.focus_goals 与默认值合并；脏值/缺档回落默认。"""
    stored = (user.settings or {}).get("focus_goals") or {}
    out = {}
    for k, d in FOCUS_GOALS.items():
        v = stored.get(k)
        out[k] = int(v) if isinstance(v, (int, float)) and v > 0 else d
    return out


def _pct_change(cur: float, prev: float) -> float | None:
    """环比变化百分比；无基数返回 None。"""
    if prev <= 0:
        return None
    return round((cur - prev) / prev * 100)


def _bucketize(sessions: list[datetime], secs: dict, scope: str) -> dict:
    """把 focus 会话按 scope 聚合分钟数。"""
    buckets: dict[str, int] = {}
    for dt in sessions:
        if scope == "today":
            key = str(dt.hour)
        elif scope == "week":
            key = "一二三四五六日"[(dt.weekday() + 1) % 7]
        else:  # month：按第几周
            key = f"第{(dt.day - 1) // 7 + 1}期"
        buckets[key] = buckets.get(key, 0) + secs.get(dt, 0)
    return buckets


def _focus_block(cur_sec: int, prev_sec: int, goal: int) -> dict:
    return {
        "sec": cur_sec,
        "goal": goal,
        "pct": min(100, round(cur_sec / goal * 100)) if goal else 0,
        "prev_pct": _pct_change(cur_sec, prev_sec),
    }


async def _achievements(
    db: AsyncSession, user_id: uuid.UUID, cards_total: int, reviews_total: int, timezone: str = "Asia/Shanghai"
) -> list[dict]:
    """成就引擎：按真实学习记录实时计算，无额外徽章状态表。"""
    now = _utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 复习连续天数（近 200 天日志日期去重）
    rows = (
        await db.execute(
            select(ReviewLog.reviewed_at).where(
                ReviewLog.user_id == user_id,
                ReviewLog.reviewed_at >= today - _dt.timedelta(days=200),
            )
        )
    ).all()
    days = sorted({(r[0].date()) for r in rows})
    streak = 0
    if days:
        cursor = today.date() if today.date() in days else days[-1]
        if (today.date() - cursor).days <= 1:
            streak = 1
            for i in range(len(days) - 2, -1, -1):
                if (cursor - days[i]).days == 1:
                    cursor = days[i]
                    streak += 1
                elif (cursor - days[i]).days > 1:
                    break

    # 本月复习天数
    month_days = len({d for d in days if d >= month_start.date()})

    # 专注总时长 + 本月（只计完整结束或主动打断且非打盹的会话）
    focus_total = (
        await db.scalar(
            select(func.coalesce(func.sum(FocusSession.duration_seconds), 0)).where(
                FocusSession.user_id == user_id,
                _counted_focus(),
                FocusSession.mode != "nap",
            )
        )
    ) or 0
    focus_month = (
        await db.scalar(
            select(func.coalesce(func.sum(FocusSession.duration_seconds), 0)).where(
                FocusSession.user_id == user_id,
                _counted_focus(),
                FocusSession.mode != "nap",
                FocusSession.started_at >= month_start,
            )
        )
    ) or 0

    # 笔记数 / AI 调用次数
    notes_total = await db.scalar(select(func.count(Note.id)).where(Note.user_id == user_id)) or 0
    ai_total = await db.scalar(select(func.count(AiUsage.id)).where(AiUsage.user_id == user_id)) or 0

    # 单日新增卡峰值
    peak_rows = (
        await db.execute(
            select(func.count(Card.id))
            .where(Card.user_id == user_id, Card.deleted_at.is_(None))
            .group_by(func.date(Card.created_at))
            .order_by(func.count(Card.id).desc())
            .limit(1)
        )
    ).all()
    peak_cards = peak_rows[0][0] if peak_rows else 0
    files_total = await db.scalar(select(func.count(File.id)).where(
        File.user_id == user_id, File.is_dir.is_(False), File.deleted_at.is_(None),
    )) or 0
    pomodoros_total = await db.scalar(select(func.count(FocusSession.id)).where(
        FocusSession.user_id == user_id,
        FocusSession.mode == "pomodoro",
        FocusSession.completed.is_(True),
    )) or 0

    def mk(group, name, desc, icon, cur, target, rarity):
        return {
            "group": group,
            "name": name,
            "desc": desc,
            "icon": icon,
            "progress": min(cur, target),
            "target": target,
            "unlocked": cur >= target,
            "rarity": rarity,
        }

    return [
        # 坚持（连续复习天数）
        mk("坚持", "初火", "连续 3 天复习", "#i-flame", streak, 3, "铜"),
        mk("坚持", "不灭", "连续 30 天复习", "#i-star", streak, 30, "银"),
        mk("坚持", "百日炉火", "连续 100 天复习", "#i-crown", streak, 100, "金"),
        mk("坚持", "满月", "本月复习 25 天", "#i-calendar", month_days, 25, "银"),
        # 积累（卡片量）
        mk("积累", "百卡仓", "累计 100 张卡", "#i-doc", cards_total, 100, "铜"),
        mk("积累", "积少成多", "累计 10 张卡", "#i-doc", cards_total, 10, "铜"),
        mk("积累", "千卡仓", "累计 1000 张卡", "#i-library", cards_total, 1000, "银"),
        mk("积累", "一日十卡", "单日新增 10 张卡", "#i-bolt", peak_cards, 10, "铜"),
        mk("积累", "万卡仓", "累计 5000 张卡", "#i-gem", cards_total, 5000, "钻"),
        mk("积累", "书山有路", "累计上传 20 份资料", "#i-library", files_total, 20, "银"),
        # 专注（总时长）
        mk("专注", "小憩", "累计专注 1 小时", "#i-clock", focus_total, 3600, "铜"),
        mk("专注", "沉浸", "累计专注 10 小时", "#i-target", focus_total, 36000, "银"),
        mk("专注", "心流", "累计专注 50 小时", "#i-flame", focus_total, 180000, "金"),
        mk("专注", "百炼", "累计专注 100 小时", "#i-crown", focus_total, 360000, "钻"),
        # 番茄钟（完整完成次数；打断和重置不计）
        mk("番茄钟", "番茄初心", "完整完成 1 次番茄专注", "#i-clock", pomodoros_total, 1, "铜"),
        mk("番茄钟", "番茄大师", "完整完成 100 次番茄专注", "#i-crown", pomodoros_total, 100, "金"),
        # 提炼（AI 调用）
        mk("提炼", "初试啼声", "AI 提炼 1 篇笔记", "#i-md", notes_total, 1, "铜"),
        mk("提炼", "AI 拆解 100", "AI 累计调用 100 次", "#i-spark", ai_total, 100, "银"),
        mk("提炼", "十卷笔记", "提炼 10 篇笔记", "#i-book", notes_total, 10, "银"),
        mk("提炼", "AI 拆解 500", "AI 累计调用 500 次", "#i-gem", ai_total, 500, "金"),
        # 学习（资料与复习）
        mk("学习", "学而时习", "累计复习 30 次", "#i-star", reviews_total, 30, "铜"),
        mk("学习", "博览群书", "累计上传 10 份资料", "#i-book", files_total, 10, "银"),
    ] + checkin_achievements(**await checkin_summary(db, user_id, timezone))


@router.post("/achievements/claim")
async def claim_new_achievements(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Return newly unlocked badges once per account for the celebration overlay."""
    cards_total = await db.scalar(select(func.count(Card.id)).where(
        Card.user_id == user.id, Card.deleted_at.is_(None),
    )) or 0
    reviews_total = await db.scalar(select(func.count(ReviewLog.id)).where(
        ReviewLog.user_id == user.id,
    )) or 0
    badges = await _achievements(db, user.id, cards_total, reviews_total, user.timezone)
    unlocked = [badge for badge in badges if badge["unlocked"]]
    settings = dict(user.settings or {})
    stored = settings.get("announced_badges")
    # Existing accounts already have earned badges. Establish their baseline
    # silently so releasing this feature does not replay old achievements.
    if not isinstance(stored, list):
        settings["announced_badges"] = [badge["name"] for badge in unlocked]
        user.settings = settings
        await db.commit()
        return []

    seen = {name for name in stored if isinstance(name, str)}
    fresh = [badge for badge in unlocked if badge["name"] not in seen]
    if fresh:
        settings["announced_badges"] = [*dict.fromkeys(name for name in stored if isinstance(name, str)), *(badge["name"] for badge in fresh)]
        user.settings = settings
        await db.commit()
    return fresh


@router.get("/dashboard")
async def dashboard(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 用户本地时区边界（本地今天零点 / 周一零点 / 月初零点），换算成 UTC 与库中比较
    now_local = datetime.now(_user_tz(user))
    today_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start_local = today_local - _dt.timedelta(days=(now_local.weekday() + 1) % 7)  # 周一
    month_start_local = today_local.replace(day=1)
    today = today_local.astimezone(timezone.utc)
    week_start = week_start_local.astimezone(timezone.utc)
    month_start = month_start_local.astimezone(timezone.utc)

    # ── 专注：本月会话一次取出，内存聚合三卡 + 分布（计入完成与主动打断，排除打盹）──
    sess = (
        await db.execute(
            select(FocusSession.started_at, FocusSession.duration_seconds, FocusSession.deck_name).where(
                FocusSession.user_id == user.id,
                _counted_focus(),
                FocusSession.mode != "nap",
                FocusSession.started_at >= month_start,
            )
        )
    ).all()
    secs: dict[datetime, int] = {}
    today_sec = week_sec = month_sec = 0
    topics: dict[str, dict[str, int]] = {"today": {}, "week": {}, "month": {}}
    for started_at, dur, deck_name in sess:
        secs[started_at] = secs.get(started_at, 0) + dur
        name = (deck_name or "").strip() or "未指定"
        topics["month"][name] = topics["month"].get(name, 0) + dur
        month_sec += dur
        if started_at >= week_start:
            topics["week"][name] = topics["week"].get(name, 0) + dur
            week_sec += dur
        if started_at >= today:
            topics["today"][name] = topics["today"].get(name, 0) + dur
            today_sec += dur

    # prev 对比（同样计入完成与主动打断，排除打盹）
    y_start, y_end = today - _dt.timedelta(days=1), today
    w_start, w_end = week_start - _dt.timedelta(days=7), week_start
    pm_start = (month_start - _dt.timedelta(days=1)).replace(day=1)
    prev_month_sec = (
        await db.scalar(
            select(func.coalesce(func.sum(FocusSession.duration_seconds), 0)).where(
                FocusSession.user_id == user.id,
                _counted_focus(),
                FocusSession.mode != "nap",
                FocusSession.started_at >= pm_start,
                FocusSession.started_at < month_start,
            )
        )
    ) or 0
    prev_today_sec = (
        await db.scalar(
            select(func.coalesce(func.sum(FocusSession.duration_seconds), 0)).where(
                FocusSession.user_id == user.id,
                _counted_focus(),
                FocusSession.mode != "nap",
                FocusSession.started_at >= y_start,
                FocusSession.started_at < y_end,
            )
        )
    ) or 0
    prev_week_sec = (
        await db.scalar(
            select(func.coalesce(func.sum(FocusSession.duration_seconds), 0)).where(
                FocusSession.user_id == user.id,
                _counted_focus(),
                FocusSession.mode != "nap",
                FocusSession.started_at >= w_start,
                FocusSession.started_at < w_end,
            )
        )
    ) or 0

    ug = _user_focus_goals(user)
    focus = {
        "today": _focus_block(today_sec, prev_today_sec, ug["today"]),
        "week": _focus_block(week_sec, prev_week_sec, ug["week"]),
        "month": _focus_block(month_sec, prev_month_sec, ug["month"]),
        "dist_today": _bucketize([s for s in secs if s >= today], {s: secs[s] for s in secs if s >= today}, "today"),
        "dist_week": _bucketize([s for s in secs if s >= week_start], {s: secs[s] for s in secs if s >= week_start}, "week"),
        "dist_month": _bucketize([s for s in secs], secs, "month"),
        "topics": {
            period: [
                {"name": name, "sec": sec}
                for name, sec in sorted(values.items(), key=lambda pair: (-pair[1], pair[0]))
            ]
            for period, values in topics.items()
        },
    }

    # ── 指标行 ──
    total_reviews = await db.scalar(select(func.count(ReviewLog.id)).where(ReviewLog.user_id == user.id)) or 0
    cards_total = await db.scalar(
        select(func.count(Card.id)).where(Card.user_id == user.id, Card.deleted_at.is_(None))
    ) or 0
    r30 = (
        await db.execute(
            select(ReviewLog.rating, func.count(ReviewLog.id)).where(
                ReviewLog.user_id == user.id,
                ReviewLog.reviewed_at >= today - _dt.timedelta(days=30),
            ).group_by(ReviewLog.rating)
        )
    ).all()
    r30_map = {r: n for r, n in r30}
    acc30 = round(
        (r30_map.get(3, 0) + r30_map.get(4, 0)) / max(1, sum(r30_map.values())) * 100
    )
    ai_month = await db.scalar(
        select(func.count(AiUsage.id)).where(
            AiUsage.user_id == user.id, AiUsage.created_at >= month_start
        )
    ) or 0

    # ── 遗忘曲线：平均记忆稳定性（review/relearning 态）──
    avg_stability = await db.scalar(
        select(func.avg(CardState.stability))
        .join(Card, CardState.card_id == Card.id)
        .where(
            CardState.stability.is_not(None),
            Card.user_id == user.id,
            Card.state.in_(("review", "relearning")),
            Card.deleted_at.is_(None),
        )
    )

    # ── 卡组健康度：毕业率（review/relearning 占比）──
    deck_rows = (
        await db.execute(
            select(
                Deck.name,
                func.count(Card.id),
                func.sum(case((Card.state.in_(("review", "relearning")), 1), else_=0)),
            )
            .join(Card, (Card.deck_id == Deck.id) & (Card.deleted_at.is_(None)))
            .where(Deck.user_id == user.id)
            .group_by(Deck.id, Deck.name)
            .order_by(func.count(Card.id).desc())
            .limit(6)
        )
    ).all()
    deck_health = [
        {"name": name, "pct": round(rev / total * 100) if total else 0}
        for name, total, rev in deck_rows
        if total
    ]

    achievements = await _achievements(db, user.id, cards_total, total_reviews, user.timezone)

    return {
        "focus": focus,
        "metrics": {
            "total_reviews": total_reviews,
            "accuracy_30d": acc30,
            "cards_total": cards_total,
            "ai_calls_month": ai_month,
        },
        "avg_stability": avg_stability,
        "deck_health": deck_health,
        "achievements": achievements,
    }
