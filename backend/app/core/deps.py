"""依赖注入：数据库会话、当前用户。"""
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.exceptions import unauthorized
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise unauthorized("缺少访问令牌")
    try:
        payload = security.decode_token(creds.credentials)
    except JWTError:
        raise unauthorized("令牌无效或已过期")

    if payload.get("type") != security.ACCESS_TYPE:
        raise unauthorized("令牌类型错误")

    sub = payload.get("sub")
    try:
        user_id = uuid.UUID(sub)
    except (ValueError, TypeError):
        raise unauthorized("令牌载荷非法")

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise unauthorized("用户不存在或已停用")
    return user
