"""认证接口：注册 / 登录 / 刷新 / 登出 / 当前用户 / 头像 / 专注目标。"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.exceptions import AppError, conflict, unauthorized
from app.models.user import RefreshToken, User
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut
from app.schemas.user import AvatarOut, FocusTopicIn, GoalsIn, UserOut, UserUpdate
from app.services.storage import storage

router = APIRouter(prefix="/auth", tags=["auth"])

# 头像约束：格式与大小（2MB 足够头像用）
AVATAR_EXTS = {"png", "jpg", "jpeg", "webp"}
AVATAR_MIME = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
AVATAR_MAX_BYTES = 2 * 1024 * 1024

# 专注目标默认值与可设置范围（秒）
GOAL_DEFAULTS = {"today": 3 * 3600, "week": 20 * 3600, "month": 80 * 3600}
GOAL_LIMITS = {"today": (600, 86400), "week": (3600, 604800), "month": (86400, 2_592_000)}


def _goal_settings(user: User) -> dict:
    return dict(user.settings or {})


def _goals_out(user: User) -> dict:
    """settings.focus_goals 与默认值合并后的对外视图（缺档回落默认）。"""
    stored = _goal_settings(user).get("focus_goals") or {}
    out = {}
    for k, d in GOAL_DEFAULTS.items():
        v = stored.get(k)
        out[k] = int(v) if isinstance(v, (int, float)) and v > 0 else d
    return out


def _hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


async def _store_refresh_token(db: AsyncSession, user: User, jti: str) -> None:
    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_jti(jti),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    await db.flush()


async def _issue_tokens(db: AsyncSession, user: User) -> TokenOut:
    refresh_token, jti = security.create_refresh_token(str(user.id))
    await _store_refresh_token(db, user, jti)
    return TokenOut(
        access_token=security.create_access_token(str(user.id)),
        refresh_token=refresh_token,
    )


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    email = body.email.lower()
    exists = await db.scalar(
        select(User.id).where((User.email == email) | (User.username == body.username))
    )
    if exists:
        raise conflict("邮箱或用户名已被占用")

    user = User(
        email=email,
        username=body.username,
        hashed_password=security.hash_password(body.password),
        settings={"announced_badges": []},
    )
    db.add(user)
    await db.flush()
    tokens = await _issue_tokens(db, user)
    await db.commit()
    return tokens


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    account = body.account.lower()
    user = await db.scalar(
        select(User).where((User.email == account) | (User.username == body.account))
    )
    if user is None or not security.verify_password(body.password, user.hashed_password):
        raise unauthorized("账号或密码错误")
    if not user.is_active:
        raise unauthorized("账号已停用")

    tokens = await _issue_tokens(db, user)
    await db.commit()
    return tokens


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_db)):
    try:
        payload = security.decode_token(body.refresh_token)
    except JWTError:
        raise unauthorized("刷新令牌无效或已过期")

    if payload.get("type") != security.REFRESH_TYPE:
        raise unauthorized("令牌类型错误")

    jti = payload.get("jti")
    if not jti:
        raise unauthorized("令牌载荷非法")

    stored = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == _hash_jti(jti))
    )
    if stored is None or stored.revoked_at is not None:
        raise unauthorized("刷新令牌已吊销")

    user = await db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise unauthorized("用户不存在或已停用")

    # 轮换：吊销旧刷新令牌，签发新的
    stored.revoked_at = datetime.now(timezone.utc)
    tokens = await _issue_tokens(db, user)
    await db.commit()
    return tokens


@router.post("/logout", status_code=204)
async def logout(
    body: RefreshIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        payload = security.decode_token(body.refresh_token)
        jti = payload.get("jti")
        if jti:
            stored = await db.scalar(
                select(RefreshToken).where(RefreshToken.token_hash == _hash_jti(jti))
            )
            if stored and stored.revoked_at is None:
                stored.revoked_at = datetime.now(timezone.utc)
    except JWTError:
        pass  # 令牌本身无效也算登出成功
    await db.commit()


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    changed = False
    if body.timezone is not None:
        try:
            ZoneInfo(body.timezone)
        except Exception:
            raise AppError(422, "INVALID_TIMEZONE", "无效的时区")
        user.timezone = body.timezone
        changed = True
    if body.username is not None:
        name = body.username.strip()
        if not 1 <= len(name) <= 32:
            raise AppError(422, "INVALID_USERNAME", "用户名要 1-32 个字符")
        if name != user.username:
            dup = await db.scalar(select(User.id).where(User.username == name, User.id != user.id))
            if dup:
                raise conflict("用户名已被占用")
            user.username = name
            changed = True
    if changed:
        await db.commit()
        await db.refresh(user)
    return user


@router.post("/me/avatar", response_model=AvatarOut)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """头像上传：存 storage/avatars/{uid}.{ext}，版本号记在 settings.avatar_v 供前端刷新。"""
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in AVATAR_EXTS:
        raise AppError(415, "UNSUPPORTED_IMAGE", "头像只支持 png / jpg / webp")
    data = await file.read()
    if not data:
        raise AppError(422, "EMPTY_FILE", "文件是空的")
    if len(data) > AVATAR_MAX_BYTES:
        raise AppError(413, "IMAGE_TOO_LARGE", "头像别超过 2MB")

    s = _goal_settings(user)
    v = int(s.get("avatar_v") or 0) + 1
    s["avatar_ext"] = ext
    s["avatar_v"] = v
    user.settings = s  # 重新赋值，确保 JSON 列变更被追踪
    storage.put(f"avatars/{user.id}.{ext}", data)
    await db.commit()
    return AvatarOut(avatar_v=v, avatar_ext=ext)


@router.get("/me/avatar")
async def get_avatar(user: User = Depends(get_current_user)):
    s = _goal_settings(user)
    ext = s.get("avatar_ext")
    if not ext or ext not in AVATAR_MIME:
        raise AppError(404, "NO_AVATAR", "还没有上传过头像")
    try:
        data = storage.get(f"avatars/{user.id}.{ext}")
    except (FileNotFoundError, OSError):
        raise AppError(404, "NO_AVATAR", "头像文件不见了，重新传一张吧")
    return Response(content=data, media_type=AVATAR_MIME[ext])


@router.get("/me/goals")
async def get_goals(user: User = Depends(get_current_user)):
    return _goals_out(user)


@router.patch("/me/goals")
async def update_goals(
    body: GoalsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """专注目标（秒）：三档互相独立，None 的档不动。"""
    for k, (lo, hi) in GOAL_LIMITS.items():
        v = getattr(body, k)
        if v is not None and not lo <= v <= hi:
            label = {"today": "今日", "week": "本周", "month": "本月"}[k]
            raise AppError(422, "INVALID_GOAL", f"{label}目标超出可设置范围")
    s = _goal_settings(user)
    stored = dict(s.get("focus_goals") or {})
    for k in GOAL_LIMITS:
        v = getattr(body, k)
        if v is not None:
            stored[k] = int(v)
    s["focus_goals"] = stored
    user.settings = s
    await db.commit()
    return _goals_out(user)


def _focus_topics(user: User) -> list[str]:
    raw = (user.settings or {}).get("focus_topics") or []
    return [name for name in raw if isinstance(name, str) and name.strip()][:30]


@router.get("/me/focus-topics", response_model=list[str])
async def get_focus_topics(user: User = Depends(get_current_user)):
    return _focus_topics(user)


@router.post("/me/focus-topics", response_model=list[str])
async def remember_focus_topic(
    body: FocusTopicIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    label = body.label.strip()
    if not 1 <= len(label) <= 120:
        raise AppError(422, "INVALID_FOCUS_TOPIC", "专注内容需为 1-120 个字符")
    names = [name for name in _focus_topics(user) if name.casefold() != label.casefold()]
    updated = [label, *names][:30]
    user.settings = {**(user.settings or {}), "focus_topics": updated}
    await db.commit()
    return updated


@router.delete("/me/focus-topics", response_model=list[str])
async def forget_focus_topic(
    body: FocusTopicIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated = [name for name in _focus_topics(user) if name != body.label]
    user.settings = {**(user.settings or {}), "focus_topics": updated}
    await db.commit()
    return updated
