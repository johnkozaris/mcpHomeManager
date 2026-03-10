"""Dialect-aware engine factory for SQLite and PostgreSQL."""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool


def create_configured_engine(url: str, *, is_sqlite: bool) -> AsyncEngine:
    """Create an async engine with all dialect-specific configuration applied."""
    if is_sqlite:
        engine = create_async_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        _attach_sqlite_pragmas(engine)
        return engine
    return create_async_engine(url)


def _attach_sqlite_pragmas(engine: AsyncEngine) -> None:
    """Attach WAL mode and other performance/correctness PRAGMAs for SQLite."""

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragmas(dbapi_conn: object, connection_record: object) -> None:
        cursor = dbapi_conn.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
