"""
Database connection for AP Studios.
Supports sync (psycopg2) and async (asyncpg) via SQLAlchemy 2.0.
Falls back gracefully if DATABASE_URL is not set (dev without Docker).
"""
from __future__ import annotations

import logging
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://apstudios:apstudios@localhost:5432/apstudios",
)

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )
    DB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Database not available: {e}. Falling back to file storage.")
    engine = None
    DB_AVAILABLE = False

SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency - yields a DB session."""
    if not SessionLocal:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_db_available() -> bool:
    """Check si Postgres está disponible en runtime."""
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
