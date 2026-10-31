"""
Database Engine, Session Management, and Base Declarative Model.
Uses SQLAlchemy 2.0 with PyMySQL for MySQL 8.0+, with resilient fallback handling.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

uri = settings.SQLALCHEMY_DATABASE_URI
if "sqlite" in uri:
    engine = create_engine(
        uri,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(
        uri,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=False,
    )

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Automatically closes the session when the request completes.
    Rolls back automatically if an unhandled exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session rolled back due to error: {e}")
        raise
    finally:
        db.close()


def check_db_connection() -> dict:
    """
    Diagnostic utility to test live database connection and retrieve engine info.
    """
    try:
        with engine.connect() as conn:
            if "sqlite" in settings.SQLALCHEMY_DATABASE_URI:
                result = conn.execute(text("SELECT sqlite_version();"))
                row = result.fetchone()
                return {
                    "status": "connected",
                    "database_engine": "SQLite",
                    "version": row[0] if row else "unknown",
                    "current_database": "local_sqlite",
                }
            result = conn.execute(text("SELECT VERSION() as version, DATABASE() as db_name;"))
            row = result.fetchone()
            return {
                "status": "connected",
                "database_engine": "MySQL 8.0+",
                "version": row[0] if row else "unknown",
                "current_database": row[1] if row else settings.DB_NAME,
            }
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {
            "status": "error",
            "database_engine": "MySQL 8.0+",
            "error": str(e),
        }
