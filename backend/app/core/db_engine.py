"""
Async SQLAlchemy database engine factory.

USAGE
-----
In development the engine points to the local SQLite file (default, requires
`aiosqlite` which is bundled with sqlalchemy[asyncio]).

In production set DATABASE_URL to a PostgreSQL connection string:
  DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

The rest of the application should obtain sessions via `get_async_session`
and never open raw sqlite3 connections directly.

MIGRATION PATH
--------------
The existing services (auth_service.py, sqlite_service.py) still use raw
sqlite3. Migration steps:
  1. Replace raw sqlite3 calls with SQLAlchemy ORM / core expressions.
  2. Import `async_session_factory` and use `async with async_session_factory() as session`.
  3. Remove sqlite_service.py and auth_service.py raw connection helpers.
"""
import logging
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.core.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "contracts.db"


def _build_url() -> str:
    """
    Return the database URL to use.
    Normalises legacy sqlite:// URLs so they work with the async driver.
    """
    url = settings.DATABASE_URL.strip()
    if not url:
        # Default: local SQLite
        _DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite+aiosqlite:///{_DEFAULT_SQLITE_PATH}"
    elif url.startswith("sqlite:///"):
        # Convert bare sqlite:// to async variant
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    elif url.startswith("postgresql://"):
        # Convert legacy scheme to asyncpg
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_url = _build_url()
_is_sqlite = _url.startswith("sqlite")

logger.info(f"Database engine: {'SQLite (local)' if _is_sqlite else 'PostgreSQL'}")

# SQLite needs StaticPool + connect_args to work safely in async context
_engine_kwargs: dict = {}
if _is_sqlite:
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

engine = create_async_engine(
    _url,
    echo=(os.getenv("SQL_ECHO", "false").lower() == "true"),
    **_engine_kwargs,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:
    """FastAPI dependency — yields a database session and commits/rolls back."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
