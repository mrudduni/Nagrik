from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_async_session_maker = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL
        # If asyncpg isn't installed and URL specifies asyncpg, log helpful message
        try:
            _engine = create_async_engine(
                db_url,
                echo=False,
                future=True,
            )
        except Exception as e:
            logger.warning(f"Could not initialize primary database engine ({db_url}): {e}. Using SQLite in-memory.")
            _engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    return _engine


def get_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_maker


# Compatibility alias
class _AsyncSessionMakerProxy:
    def __call__(self, *args, **kwargs):
        return get_session_maker()(*args, **kwargs)


async_session_maker = _AsyncSessionMakerProxy()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
