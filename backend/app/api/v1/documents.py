"""文档接口：解析状态、正文、重解析。"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import not_found
from app.models.file import Document, File
from app.models.user import User
from app.schemas.file import DocumentContentOut, DocumentOut
from app.services import parser
from app.services.storage import storage

router = APIRouter(prefix="/documents", tags=["documents"])


async def _get_doc(db: AsyncSession, user_id: uuid.UUID, doc_id: uuid.UUID) -> Document:
    doc = await db.scalar(select(Document).where(Document.id == doc_id, Document.user_id == user_id))
    if doc is None:
        raise not_found("文档不存在")
    return doc


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return DocumentOut.model_validate(await _get_doc(db, user.id, doc_id))


@router.get("/{doc_id}/content", response_model=DocumentContentOut)
async def get_content(
    doc_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    doc = await _get_doc(db, user.id, doc_id)
    return DocumentContentOut(
        document_id=doc.id,
        file_id=doc.file_id,
        title=doc.title,
        page_count=doc.page_count,
        text=doc.text or "",
    )


@router.post("/{doc_id}/reparse", response_model=DocumentOut)
async def reparse(
    doc_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    doc = await _get_doc(db, user.id, doc_id)
    f = await db.scalar(
        select(File).where(File.id == doc.file_id, File.user_id == user.id, File.deleted_at.is_(None))
    )
    if f is None:
        raise not_found("源文件已删除")

    doc.status = "parsing"
    doc.error = None
    try:
        data = storage.get(f.storage_path)
        text, page_count = parser.extract_text(f.name, data)
        doc.text = text
        doc.page_count = page_count
        doc.status = "done"
    except Exception as e:
        doc.status = "failed"
        doc.error = str(e)

    await db.commit()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)
