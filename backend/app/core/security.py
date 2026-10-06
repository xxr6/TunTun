"""安全：密码哈希（bcrypt）与 JWT 签发/校验。

说明：不用 passlib——它已停止维护，且依赖 Python 3.13 已移除的 crypt 标准库。
bcrypt 库本身即可满足需求。
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TYPE = "access"
REFRESH_TYPE = "refresh"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta, jti: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if jti:
        payload["jti"] = jti
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=ACCESS_TYPE,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """返回 (refresh_token, jti)。jti 用于入库以便吊销。"""
    jti = uuid.uuid4().hex
    token = _create_token(
        subject=user_id,
        token_type=REFRESH_TYPE,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        jti=jti,
    )
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """解码并校验签名/过期。失败抛 JWTError。"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
