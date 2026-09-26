from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from demo_api.models import Base

DATABASE_URL = "sqlite+aiosqlite:///./demo_ledger.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        # SQLite WAL concurrency and relational integrity PRAGMAs
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA busy_timeout=5000;"))
        await conn.execute(text("PRAGMA foreign_keys=ON;"))
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """FastAPI dependency yielding isolated sessions with explicit rollback guards (FIN-006)."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
