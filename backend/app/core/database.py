import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Default to SQLite unless PostgreSQL is explicitly configured and working
_engine = None
_sessionmaker = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.SQLITE_URL,
            echo=False,
            future=True,
        )
    return _engine

def get_sessionmaker():
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _sessionmaker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous SQLAlchemy session."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

from sqlalchemy import text

def _run_sqlite_column_migrations(connection):
    """Safely adds missing columns to existing tables for backwards-compatible SQLite schemas."""
    try:
        tables_cols = {
            "form_sessions": [
                ("guest_session_id", "VARCHAR(64)"),
                ("signature_path", "VARCHAR(512)"),
                ("style_preferences", "JSON"),
            ],
            "form_templates": [
                ("guest_session_id", "VARCHAR(64)"),
            ],
            "uploaded_documents": [
                ("guest_session_id", "VARCHAR(64)"),
            ],
        }
        for table, cols in tables_cols.items():
            try:
                res = connection.execute(text(f"PRAGMA table_info({table})")).fetchall()
                existing = [row[1] for row in res]
                for col_name, col_type in cols:
                    if col_name not in existing:
                        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                        logger.info(f"Added missing column '{col_name}' to table '{table}'")
            except Exception as te:
                logger.debug(f"Table {table} check: {te}")
    except Exception as e:
        logger.warning(f"Column migration note: {e}")

async def init_db():
    """Initializes database tables on active engine."""
    global _engine, _sessionmaker

    # If DATABASE_URL is set and not empty, test PostgreSQL connection
    if settings.DATABASE_URL and "postgresql" in settings.DATABASE_URL:
        try:
            test_engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            _engine = test_engine
            _sessionmaker = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
            logger.info("Connected to PostgreSQL successfully.")
            return
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite for local development.")

    # SQLite fallback
    _engine = create_async_engine(settings.SQLITE_URL, echo=False, future=True)
    _sessionmaker = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_run_sqlite_column_migrations)
    logger.info("Initialized local SQLite database fallback successfully.")
