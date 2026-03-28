"""
Auto-migration on startup.
Creates tables if they don't exist.
For schema changes use Alembic (configured separately).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_migrations() -> bool:
    """
    Create all tables on first run.
    Safe to call multiple times (CREATE TABLE IF NOT EXISTS).
    Returns True if DB is available, False if not.
    """
    try:
        from app.database.connection import DB_AVAILABLE, engine
        from app.database.models import Base

        if not DB_AVAILABLE or not engine:
            logger.info("DB not available — skipping migrations, using file storage")
            return False

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified OK")
        return True
    except Exception as e:
        logger.warning(f"Migration failed (will use file storage): {e}")
        return False
