"""卡组接口：树形 CRUD。"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import not_found
from app.models.card import Card
from app.models.deck import Deck
from app.models.user import User
from app.schemas.deck import DeckCreate, DeckMove, DeckOut, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


async def _get_deck(db: AsyncSession, user_id: uuid.UUID, deck_id: uuid.UUID) -> Deck:
    deck = await db.scalar(select(Deck).where(Deck.id == deck_id, Deck.user_id == user_id))
    if deck is None:
        raise not_found("卡组不存在")
    return deck


@router.get("", response_model=list[DeckOut])
async def list_decks(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    decks = (
        await db.scalars(
            select(Deck).where(Deck.user_id == user.id).order_by(Deck.position, Deck.created_at)
        )
    ).all()
    rows = (
        await db.execute(
            select(Card.deck_id, func.count(Card.id))
            .where(Card.user_id == user.id, Card.deleted_at.is_(None))
            .group_by(Card.deck_id)
        )
    ).all()
    counts = {deck_id: n for deck_id, n in rows}

    out: list[DeckOut] = []
    for d in decks:
        o = DeckOut.model_validate(d)
        o.card_count = counts.get(d.id, 0)
        out.append(o)
    return out


@router.post("", response_model=DeckOut, status_code=201)
async def create_deck(body: DeckCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.parent_id is not None:
        await _get_deck(db, user.id, body.parent_id)
    deck = Deck(
        user_id=user.id,
        name=body.name,
        parent_id=body.parent_id,
        description=body.description,
        config=body.config,
    )
    db.add(deck)
    await db.commit()
    await db.refresh(deck)
    return DeckOut.model_validate(deck)


@router.get("/{deck_id}", response_model=DeckOut)
async def get_deck(
    deck_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    deck = await _get_deck(db, user.id, deck_id)
    count = await db.scalar(
        select(func.count(Card.id)).where(
            Card.deck_id == deck_id, Card.user_id == user.id, Card.deleted_at.is_(None)
        )
    )
    out = DeckOut.model_validate(deck)
    out.card_count = count or 0
    return out


@router.patch("/{deck_id}", response_model=DeckOut)
async def update_deck(
    deck_id: uuid.UUID,
    body: DeckUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(db, user.id, deck_id)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(deck, k, v)
    await db.commit()
    await db.refresh(deck)
    return DeckOut.model_validate(deck)


@router.post("/{deck_id}/move", response_model=DeckOut)
async def move_deck(
    deck_id: uuid.UUID,
    body: DeckMove,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deck = await _get_deck(db, user.id, deck_id)
    if body.parent_id is not None:
        if body.parent_id == deck_id:
            from app.core.exceptions import conflict

            raise conflict("不能把卡组移动到自己下面")
        await _get_deck(db, user.id, body.parent_id)
    deck.parent_id = body.parent_id
    await db.commit()
    await db.refresh(deck)
    return DeckOut.model_validate(deck)


@router.delete("/{deck_id}", status_code=204)
async def delete_deck(
    deck_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    deck = await _get_deck(db, user.id, deck_id)
    await db.delete(deck)  # 级联删除子卡组与卡片（FK ondelete CASCADE）
    await db.commit()
