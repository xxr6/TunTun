"""初始化数据库：开发期用 create_all 快速建表。

正式部署走 Alembic 迁移（alembic upgrade head）。M1 阶段先用 create_all 兜底，
后续每个数据模型落地后同步补 Alembic 迁移。
"""
import logging

from sqlalchemy.engine import Connection

from app.db.base import Base
from app.db.session import engine

# 导入所有模型，确保注册到 Base.metadata
from app.models import ai_usage, card, checkin, deck, file, focus, note, plan, user  # noqa: F401

logger = logging.getLogger(__name__)


def _backfill_focus_columns(sync_conn: Connection) -> None:
    """给已存在的 focus_sessions 表补 deck_id/deck_name 列（幂等）。

    create_all 不会给已建好的表加新列；SQLite 开发库在这里手动补列，
    PostgreSQL 需要正式迁移（Alembic），此处跳过并打日志说明。
    """
    if sync_conn.dialect.name != "sqlite":
        logger.info("focus_sessions 的 deck_id/deck_name 列需要正式迁移（Alembic），跳过自动补列")
        return
    cols = {row[1] for row in sync_conn.exec_driver_sql("PRAGMA table_info(focus_sessions)")}
    if "deck_id" not in cols:
        sync_conn.exec_driver_sql("ALTER TABLE focus_sessions ADD COLUMN deck_id CHAR(32)")
        logger.info("focus_sessions 已补列 deck_id CHAR(32)")
    if "deck_name" not in cols:
        sync_conn.exec_driver_sql(
            "ALTER TABLE focus_sessions ADD COLUMN deck_name VARCHAR(120) NOT NULL DEFAULT ''"
        )
        logger.info("focus_sessions 已补列 deck_name VARCHAR(120) NOT NULL DEFAULT ''")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_backfill_focus_columns)
