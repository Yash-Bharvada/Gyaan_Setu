"""SQLAlchemy engine, session factory and `get_db` dependency."""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _set_sqlite_pragmas(dbapi_conn, connection_record):  # noqa: ARG001
    """Enable WAL mode + foreign keys for every SQLite connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def build_engine(url: str | None = None):
    db_url = url or settings.DB_URL
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(db_url, connect_args=connect_args, echo=False)
    if db_url.startswith("sqlite"):
        event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (idempotent)."""
    # Import all models so Base picks them up
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
