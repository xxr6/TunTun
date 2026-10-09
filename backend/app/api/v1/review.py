"""复习接口：到期队列、评分调度、撤销、到期预测。"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.exceptions import AppError, not_found
from app.models.card import Card, CardState, ReviewLog
from app.models.deck import Deck
from app.models.user import User
from app.schemas.review import (
    ReviewAnswer,
    ReviewAnswerOut,
    ReviewCard,
    ReviewQueueOut,
    ReviewUndoOut,
)
from app.services.srs.scheduler import ReviewScheduler
from app.services.card_quality import card_quality_error, reviewable

router = APIRouter(prefix="/review", tags=["review"])

scheduler = ReviewScheduler()

# 参与调度的活跃状态
_ACTIVE_STATES = ("new", "learning", "review", "relearning")


def _study_ready_sql():
    return (
        (func.length(func.trim(Card.front)) > 0)
        & (
        ((Card.card_type == "cloze") & Card.front.like("%{{c%::%}}%"))
        | ((Card.card_type != "cloze") & (func.length(func.trim(Card.back)) > 0))
        )
    )


async def _active_card(db: AsyncSession, user_id: uuid.UUID, card_id: uuid.UUID) -> Card:
    card = await db.scalar(
        select(Card)
        .options(selectinload(Card.state_info))
        .where(Card.id == card_id, Card.user_id == user_id, Card.deleted_at.is_(None))
    )
    if card is None:
        raise not_found("卡片不存在")
    return card


async def _remaining_today(db: AsyncSession, user_id: uuid.UUID) -> int:
    now = datetime.now(timezone.utc)
    rows = (await db.execute(
        select(Card.card_type, Card.front, Card.back).where(
            Card.user_id == user_id,
            Card.deleted_at.is_(None),
            Card.state.in_(_ACTIVE_STATES),
            Card.due <= now,
        )
    )).all()
    return sum(reviewable(card_type, front, back) for card_type, front, back in rows)


async def _needs_repair(db: AsyncSession, user_id: uuid.UUID, deck_id: uuid.UUID | None) -> int:
    conds = [Card.user_id == user_id, Card.deleted_at.is_(None), Card.state.in_(_ACTIVE_STATES)]
    if deck_id is not None:
        conds.append(Card.deck_id == deck_id)
    rows = (await db.execute(select(Card.card_type, Card.front, Card.back).where(*conds))).all()
    return sum(not reviewable(card_type, front, back) for card_type, front, back in rows)


@router.get("/queue", response_model=ReviewQueueOut)
async def queue(
    deck_id: uuid.UUID | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    conds = [
        Card.user_id == user.id,
        Card.deleted_at.is_(None),
        Card.state.in_(_ACTIVE_STATES),
        Card.due <= now,
        _study_ready_sql(),
    ]
    if deck_id is not None:
        conds.append(Card.deck_id == deck_id)

    cards = (
        await db.scalars(
            select(Card)
            .options(selectinload(Card.state_info))
            .where(*conds)
            .order_by(Card.due.asc())
        )
    ).all()
    cards = [c for c in cards if reviewable(c.card_type, c.front, c.back)][:limit]

    deck_ids = {c.deck_id for c in cards}
    deck_names: dict[uuid.UUID, str] = {}
    if deck_ids:
        rows = (
            await db.execute(select(Deck.id, Deck.name).where(Deck.id.in_(deck_ids)))
        ).all()
        deck_names = {did: name for did, name in rows}

    items = [
        ReviewCard(
            card_id=c.id,
            deck_id=c.deck_id,
            deck_name=deck_names.get(c.deck_id, ""),
            card_type=c.card_type,
            front=c.front,
            back=c.back,
            hint=c.hint,
            tags=c.tags or [],
            state=c.state,
            reps=(c.state_info.reps if c.state_info else 0),
            due=c.due,
            source_file_id=c.source_file_id,
            source_locator=c.source_locator,
        )
        for c in cards
    ]
    return ReviewQueueOut(
        items=items,
        remaining_today=await _remaining_today(db, user.id),
        needs_repair=await _needs_repair(db, user.id, deck_id),
    )


@router.post("/answer", response_model=ReviewAnswerOut)
async def answer(
    body: ReviewAnswer, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    now = body.reviewed_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    card = await _active_card(db, user.id, body.card_id)
    error = card_quality_error(card.card_type, card.front, card.back)
    if error:
        raise AppError(422, "CARD_NEEDS_ANSWER", error)
    cs = card.state_info
    if cs is None:
        cs = CardState(card_id=card.id, step=0, reps=0, lapses=0)
        card.state_info = cs

    # before 快照（供撤销）
    state_before = card.state
    stab_before = cs.stability
    diff_before = cs.difficulty
    due_before = card.due
    last_review_before = cs.last_review

    result = scheduler.review(
        state=card.state,
        step=cs.step,
        stability=cs.stability,
        difficulty=cs.difficulty,
        last_review=cs.last_review,
        rating=body.rating,
        now=now,
    )

    # 写回卡片与调度状态
    card.state = result["state"]
    card.due = result["due"]
    cs.step = result["step"]
    cs.stability = result["stability"]
    cs.difficulty = result["difficulty"]
    cs.last_review = now
    cs.reps += 1
    if body.rating == 1:
        cs.lapses += 1
    cs.elapsed_days = result["elapsed_days"]
    cs.scheduled_days = result["scheduled_days"]

    # 记录完整 before/after 快照，供撤销
    db.add(
        ReviewLog(
            card_id=card.id,
            user_id=user.id,
            rating=body.rating,
            state_before=state_before,
            state_after=result["state"],
            stability_before=stab_before,
            stability_after=result["stability"],
            difficulty_before=diff_before,
            difficulty_after=result["difficulty"],
            due_before=due_before,
            due_after=result["due"],
            last_review_before=last_review_before,
            elapsed_days=result["elapsed_days"],
            scheduled_days=result["scheduled_days"],
            review_duration_ms=body.duration_ms,
            reviewed_at=now,
        )
    )
    await db.commit()

    return ReviewAnswerOut(
        card_id=card.id,
        state=result["state"],
        due=result["due"],
        stability=result["stability"],
        difficulty=result["difficulty"],
        scheduled_days=result["scheduled_days"],
        remaining_today=await _remaining_today(db, user.id),
    )


@router.post("/undo", response_model=ReviewUndoOut)
async def undo(
    card_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    log = await db.scalar(
        select(ReviewLog)
        .where(ReviewLog.card_id == card_id, ReviewLog.user_id == user.id)
        .order_by(ReviewLog.reviewed_at.desc())
        .limit(1)
    )
    if log is None:
        return ReviewUndoOut(undone=False, card_id=card_id)

    card = await _active_card(db, user.id, card_id)
    cs = card.state_info
    if cs is not None:
        cs.stability = log.stability_before
        cs.difficulty = log.difficulty_before
        cs.last_review = log.last_review_before
        cs.reps = max(0, cs.reps - 1)
        if log.rating == 1:
            cs.lapses = max(0, cs.lapses - 1)
    card.state = log.state_before
    card.due = log.due_before
    await db.delete(log)
    await db.commit()
    return ReviewUndoOut(undone=True, card_id=card_id)


@router.get("/forecast")
async def forecast(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """未来 N 天每天到期的卡片数（含今天已到期未复习的）。"""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today + timedelta(days=days)

    rows = (
        await db.execute(
            select(Card.card_type, Card.front, Card.back, Card.due)
            .where(
                Card.user_id == user.id,
                Card.deleted_at.is_(None),
                Card.state.in_(_ACTIVE_STATES),
                Card.due < end,
            )
        )
    ).all()

    buckets = [0] * days
    for card_type, front, back, due in rows:
        if not reviewable(card_type, front, back):
            continue
        idx = int((due - today).total_seconds() // 86400)
        if 0 <= idx < days:
            buckets[idx] += 1

    return [{"date": (today + timedelta(days=i)).date().isoformat(), "count": buckets[i]} for i in range(days)]
