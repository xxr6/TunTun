"""AI 调用用量记录（统计页「AI 用量」卡的数据源）。"""
import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class AiUsage(Base, TimestampMixin):
    __tablename__ = "ai_usage"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    # selection = 划词成卡；extract = AI 提炼
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
