"""卡片接口：CRUD + 批量操作。"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import AppError, not_found
from app.models.card import Card, CardState
from app.models.deck import Deck
from app.models.user import User
from app.schemas.card import CardBulkAction, CardCreate, CardListOut, CardOut, CardUpdate
from app.services.card_quality import card_quality_error

router = APIRouter(prefix="/cards", tags=["cards"])

# 未指定卡组时卡片落入的默认卡组
DEFAULT_DECK_NAME = "收件箱"


async def _default_deck_id(db: AsyncSession, user_id: uuid.UUID) -> uuid.UUID:
    """取用户默认卡组；不存在则创建「收件箱」。"""
    deck = await db.scalar(
        select(Deck).where(Deck.user_id == user_id, Deck.name == DEFAULT_DECK_NAME)
    )
    if deck is not None:
        return deck.id
    deck = Deck(user_id=user_id, name=DEFAULT_DECK_NAME, description="划词成卡 / 快速入库的默认卡组")
    db.add(deck)
    await db.flush()
    return deck.id


async def _get_card(db: AsyncSession, user_id: uuid.UUID, card_id: uuid.UUID) -> Card:
    card = await db.scalar(
        select(Card).where(Card.id == card_id, Card.user_id == user_id, Card.deleted_at.is_(None))
    )
    if card is None:
        raise not_found("卡片不存在")
    return card


@router.get("", response_model=CardListOut)
async def list_cards(
    deck_id: uuid.UUID | None = None,
    source_file_id: uuid.UUID | None = None,
    tag: str | None = None,
    state: str | None = None,
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conds = [Card.user_id == user.id, Card.deleted_at.is_(None)]
    if deck_id is not None:
        conds.append(Card.deck_id == deck_id)
    if source_file_id is not None:
        conds.append(Card.source_file_id == source_file_id)
    if state is not None:
        conds.append(Card.state == state)
    if tag is not None:
        conds.append(Card.tags.contains([tag]))  # JSON 数组包含
    if q:
        conds.append(or_(Card.front.ilike(f"%{q}%"), Card.back.ilike(f"%{q}%")))

    total = await db.scalar(select(func.count(Card.id)).where(*conds)) or 0
    cards = (
        await db.scalars(
            select(Card).where(*conds).order_by(Card.created_at.desc()).limit(limit).offset(offset)
        )
    ).all()
    return CardListOut(items=[CardOut.model_validate(c) for c in cards], total=total)


@router.post("", response_model=CardOut, status_code=201)
async def create_card(body: CardCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    deck_id = body.deck_id or await _default_deck_id(db, user.id)
    deck = await db.scalar(select(Deck).where(Deck.id == deck_id, Deck.user_id == user.id))
    if deck is None:
        raise not_found("卡组不存在")

    card = Card(
        deck_id=deck_id,
        user_id=user.id,
        card_type=body.card_type,
        front=body.front,
        back=body.back,
        hint=body.hint,
        extra=body.extra,
        source_file_id=body.source_file_id,
        source_locator=body.source_locator,
        tags=body.tags,
        state="new",
        due=datetime.now(timezone.utc),
    )
    card.state_info = CardState(stability=None, difficulty=None, step=0, reps=0, lapses=0)
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return CardOut.model_validate(card)


@router.get("/{card_id}", response_model=CardOut)
async def get_card(card_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return CardOut.model_validate(await _get_card(db, user.id, card_id))


@router.patch("/{card_id}", response_model=CardOut)
async def update_card(
    card_id: uuid.UUID,
    body: CardUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    card = await _get_card(db, user.id, card_id)
    data = body.model_dump(exclude_unset=True)
    error = card_quality_error(data.get("card_type", card.card_type), data.get("front", card.front), data.get("back", card.back))
    if error:
        raise AppError(422, "CARD_NEEDS_ANSWER", error)
    for k, v in data.items():
        setattr(card, k, v)
    await db.commit()
    await db.refresh(card)
    return CardOut.model_validate(card)


@router.delete("/{card_id}", status_code=204)
async def delete_card(card_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await _get_card(db, user.id, card_id)
    card.deleted_at = datetime.now(timezone.utc)  # 软删
    await db.commit()


@router.post("/bulk", status_code=204)
async def bulk_cards(body: CardBulkAction, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cards = (
        await db.scalars(
            select(Card).where(
                Card.id.in_(body.card_ids), Card.user_id == user.id, Card.deleted_at.is_(None)
            )
        )
    ).all()
    if not cards:
        return

    if body.action == "move":
        if body.deck_id is None:
            from app.core.exceptions import conflict

            raise conflict("移动需要 deck_id")
        for c in cards:
            c.deck_id = body.deck_id
    elif body.action == "tag":
        for c in cards:
            tags = set(c.tags or [])
            for t in body.tags_remove or []:
                tags.discard(t)
            for t in body.tags_add or []:
                tags.add(t)
            c.tags = list(tags)
    elif body.action == "suspend":
        for c in cards:
            if c.state not in ("suspended", "buried"):
                c.state = "suspended"
    elif body.action == "unsuspend":
        for c in cards:
            if c.state in ("suspended", "buried"):
                c.state = "review"
    elif body.action == "delete":
        now = datetime.now(timezone.utc)
        for c in cards:
            c.deleted_at = now

    await db.commit()
