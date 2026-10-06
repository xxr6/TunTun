"""认证接口：注册 / 登录 / 刷新 / 登出 / 当前用户。"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.exceptions import AppError, conflict, unauthorized
from app.models.user import RefreshToken, User
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


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
    if body.timezone is not None:
        try:
            ZoneInfo(body.timezone)
        except Exception:
            raise AppError(422, "INVALID_TIMEZONE", "无效的时区")
        user.timezone = body.timezone
        await db.commit()
        await db.refresh(user)
    return user
