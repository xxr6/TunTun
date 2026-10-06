"""SQLAlchemy DeclarativeBase、通用混入与 UTC 时间类型。"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """跨方言的 UTC aware DateTime。

    SQLite 没有时区类型，`DateTime(timezone=True)` 读回的是 naive datetime（隐含 UTC），
    一旦和 aware datetime 做减法就会 `can't subtract offset-naive and offset-aware`。
    这个 TypeDecorator 在读写两侧都补成 UTC aware，SQLite 与 PostgreSQL 行为一致。
    所有「需要和 now() 比较/做差」的时间列一律用它。
    """
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    pass


# UUID 主键：SQLAlchemy 2.0 的 Uuid 类型自动跨方言——PG 用 native UUID，SQLite 存 CHAR(32)。
def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
