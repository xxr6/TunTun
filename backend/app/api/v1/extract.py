"""AI 提炼接口：文件 → 笔记 → 拆卡。"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import AppError, not_found
from app.models.ai_usage import AiUsage
from app.models.card import Card, CardState
from app.models.deck import Deck
from app.models.file import Document
from app.models.note import Note, NoteCandidate
from app.models.user import User
from app.schemas.extract import (
    CandidateOut,
    ExtractFromFileIn,
    NoteDetailOut,
    NoteOut,
    SplitCandidatesIn,
)
from app.services.extract import pipeline
from app.services.llm.provider import LLMError, LLMNotConfigured, get_llm

router = APIRouter(prefix="/extract", tags=["extract"])


async def _get_note(db: AsyncSession, user_id: uuid.UUID, note_id: uuid.UUID) -> Note:
    note = await db.scalar(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    )
    if note is None:
        raise not_found("笔记不存在")
    return note


def _to_detail(note: Note, cands: list[NoteCandidate]) -> NoteDetailOut:
    return NoteDetailOut(
        id=note.id,
        title=note.title,
        content_md=note.content_md,
        source_file_id=note.source_file_id,
        source_type=note.source_type,
        status=note.status,
        created_at=note.created_at,
        candidates=[CandidateOut.model_validate(c) for c in cands],
    )


@router.post("/from-file", response_model=NoteDetailOut)
async def extract_from_file(
    body: ExtractFromFileIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    doc = await db.scalar(
        select(Document).where(Document.id == body.document_id, Document.user_id == user.id)
    )
    if doc is None:
        raise not_found("文档不存在")
    if not doc.text:
        raise AppError(400, "EMPTY_DOCUMENT", "文档没有可提炼的正文，请先确保解析完成")

    llm = get_llm()
    if llm is None:
        raise AppError(503, "LLM_NOT_CONFIGURED", "未配置 LLM API Key，无法提炼。请在设置里配置。")

    try:
        content_md, cands = await pipeline.distill_document(doc.text, doc.title, llm)
    except (LLMError, LLMNotConfigured) as e:
        raise AppError(502, "LLM_FAILED", f"提炼失败：{e}")

    note = Note(
        user_id=user.id,
        source_file_id=doc.file_id,
        source_type="file",
        title=doc.title,
        content_md=content_md,
        outline={},
        status="done",
    )
    db.add(note)
    await db.flush()

    candidate_objs = [
        NoteCandidate(
            note_id=note.id,
            user_id=user.id,
            card_type=c.get("card_type", "basic"),
            front=str(c.get("front", "")),
            back=str(c.get("back", "")),
            confidence=float(c.get("confidence", 0.8)),
        )
        for c in cands
        if c.get("front")
    ]
    db.add_all(candidate_objs)
    db.add(AiUsage(user_id=user.id, kind="extract"))
    await db.commit()

    return _to_detail(note, candidate_objs)


@router.get("/notes", response_model=list[NoteOut])
async def list_notes(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    notes = (
        await db.scalars(
            select(Note).where(Note.user_id == user.id).order_by(Note.created_at.desc())
        )
    ).all()
    return [NoteOut.model_validate(n) for n in notes]


@router.get("/notes/{note_id}", response_model=NoteDetailOut)
async def get_note(
    note_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    note = await _get_note(db, user.id, note_id)
    cands = (
        await db.scalars(
            select(NoteCandidate)
            .where(NoteCandidate.note_id == note_id, NoteCandidate.user_id == user.id)
            .order_by(NoteCandidate.confidence.desc())
        )
    ).all()
    return _to_detail(note, cands)


@router.post("/notes/{note_id}/split-candidates")
async def split_candidates(
    note_id: uuid.UUID,
    body: SplitCandidatesIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await _get_note(db, user.id, note_id)
    deck = await db.scalar(select(Deck).where(Deck.id == body.deck_id, Deck.user_id == user.id))
    if deck is None:
        raise not_found("卡组不存在")

    cands = (
        await db.scalars(
            select(NoteCandidate).where(
                NoteCandidate.id.in_(body.candidate_ids),
                NoteCandidate.note_id == note_id,
                NoteCandidate.user_id == user.id,
                NoteCandidate.card_id.is_(None),
            )
        )
    ).all()

    created = 0
    for c in cands:
        card = Card(
            deck_id=body.deck_id,
            user_id=user.id,
            card_type=c.card_type,
            front=c.front,
            back=c.back,
            source_file_id=note.source_file_id,
            state="new",
            due=datetime.now(timezone.utc),
        )
        card.state_info = CardState(stability=None, difficulty=None, step=0, reps=0, lapses=0)
        db.add(card)
        await db.flush()
        c.card_id = card.id
        created += 1

    await db.commit()
    return {"created": created}
