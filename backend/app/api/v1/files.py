"""文件接口：上传、目录树、下载、重命名/移动、软删。"""
import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.exceptions import AppError, not_found
from app.models.file import Document, File
from app.models.user import User
from app.schemas.file import FileOut, FileUpdate, FolderCreate
from app.services import parser
from app.services.storage import storage

router = APIRouter(prefix="/files", tags=["files"])


async def _get_file(db: AsyncSession, user_id: uuid.UUID, file_id: uuid.UUID) -> File:
    f = await db.scalar(
        select(File).where(File.id == file_id, File.user_id == user_id, File.deleted_at.is_(None))
    )
    if f is None:
        raise not_found("文件不存在")
    return f


@router.get("", response_model=list[FileOut])
async def list_files(
    parent_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=100, description="按文件名或解析正文模糊搜索（搜正文时跨目录）"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conds = [File.user_id == user.id, File.deleted_at.is_(None)]
    if q:
        # 搜索模式：跨目录全库搜，文件名或已解析正文命中即可
        like = f"%{q}%"
        text_hit = (
            select(Document.file_id)
            .where(Document.file_id == File.id, Document.text.ilike(like))
            .exists()
        )
        conds.append(or_(File.name.ilike(like), text_hit))
    elif parent_id is not None:
        conds.append(File.parent_id == parent_id)
    else:
        conds.append(File.parent_id.is_(None))
    files = (
        await db.scalars(
            select(File).where(*conds).order_by(File.is_dir.desc(), File.created_at.desc())
        )
    ).all()
    docs = (
        await db.execute(
            select(Document.file_id, Document.id, Document.status, Document.error, Document.page_count)
            .where(Document.user_id == user.id)
        )
    ).all()
    doc_map = {fid: (did, st, err, pc) for fid, did, st, err, pc in docs}

    out: list[FileOut] = []
    for f in files:
        o = FileOut.model_validate(f)
        if not f.is_dir and f.id in doc_map:
            o.doc_id, o.doc_status, o.doc_error, o.page_count = doc_map[f.id]
        out.append(o)
    return out


@router.post("", response_model=FileOut, status_code=201)
async def upload_file(
    file: UploadFile,
    parent_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise AppError(413, "PAYLOAD_TOO_LARGE", f"文件超过 {settings.MAX_UPLOAD_MB}MB 上限")
    if not data:
        raise AppError(422, "EMPTY_FILE", "不能上传空文件")
    content_hash = hashlib.sha256(data).hexdigest()
    name = file.filename or "unnamed"
    ext = (name.rsplit(".", 1)[-1] if "." in name else "").lower()

    # 去重：同用户同内容哈希直接复用
    existing = await db.scalar(
        select(File).where(
            File.user_id == user.id,
            File.content_hash == content_hash,
            File.deleted_at.is_(None),
        )
    )
    if existing is not None:
        return FileOut.model_validate(existing)

    f = File(
        id=uuid.uuid4(),  # 显式生成主键：不依赖 flush 回填
        user_id=user.id,
        parent_id=parent_id,
        name=name,
        size=len(data),
        mime_type=file.content_type or "",
        ext=ext,
        content_hash=content_hash,
    )
    # 主键必须在这里就确定，否则 storage_path 会拼成 `.../None`：
    # ① `default=uuid.uuid4` 是 INSERT 时才求值的客户端 default，flush 之前 f.id 是 None；
    # ② 更隐蔽的是——如果 flush 因故没有回填（批量操作 / 将来换成服务端生成主键 / 异常吞掉），
    #    `.../None` 不会报错，只会让**所有文件静默撞到同一个路径互相覆盖**（历史真实事故：
    #    一个 500 之后残留了 `2026/10/None`，文件正文与 DB 记录错位）。
    # 显式给 id 后这个前提就不存在了，并且下面再加一道断言兜底。
    assert f.id is not None, "主键必须在落盘前确定"
    db.add(f)
    await db.flush()
    f.storage_path = storage.rel_path(str(user.id), str(f.id))
    storage.put(f.storage_path, data)

    # 建文档解析记录并同步解析
    doc = Document(file_id=f.id, user_id=user.id, title=name.rsplit(".", 1)[0], status="parsing")
    db.add(doc)
    await db.flush()

    try:
        text, page_count = parser.extract_text(name, data)
        doc.text = text
        doc.page_count = page_count
        doc.status = "done"
    except Exception as e:  # 解析失败不阻塞上传
        doc.status = "failed"
        doc.error = str(e)

    await db.commit()
    await db.refresh(f)
    # model_validate(f) 填不了关联文档字段（那是 list 接口的拼装逻辑），这里手动补上，
    # 否则上传响应里 doc_status 恒为 None
    o = FileOut.model_validate(f)
    o.doc_id, o.doc_status = doc.id, doc.status
    o.doc_error, o.page_count = doc.error, doc.page_count
    return o


@router.post("/folder", response_model=FileOut, status_code=201)
async def create_folder(
    body: FolderCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    f = File(user_id=user.id, parent_id=body.parent_id, name=body.name, is_dir=True)
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return FileOut.model_validate(f)


@router.get("/{file_id}/download")
async def download(
    file_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    f = await _get_file(db, user.id, file_id)
    if f.is_dir:
        raise not_found("文件夹不能下载")
    data = storage.get(f.storage_path)
    return Response(content=data, media_type=f.mime_type or "application/octet-stream")


@router.patch("/{file_id}", response_model=FileOut)
async def update_file(
    file_id: uuid.UUID,
    body: FileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await _get_file(db, user.id, file_id)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(f, k, v)
    await db.commit()
    await db.refresh(f)
    return FileOut.model_validate(f)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    f = await _get_file(db, user.id, file_id)
    f.deleted_at = datetime.now(timezone.utc)  # 软删进回收站，30 天后定时清理
    await db.commit()
