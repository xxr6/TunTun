"""异步引擎与会话工厂。"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.DB_DSN, echo=False, pool_pre_ping=True)


if settings.DB_DSN.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _record):
        """SQLite 连接级 PRAGMA：WAL 模式 + 外键。

        WAL 模式把 commit 的「delete journal 文件」换成「append 到 -wal 文件」，
        在 Windows 上避免了 journal 文件创建/删除被杀软同步扫描导致的 4-5 秒 commit 卡顿。
        """
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI 依赖：每次请求一个会话，用完回滚关闭。"""
    async with AsyncSessionLocal() as session:
        yield session
