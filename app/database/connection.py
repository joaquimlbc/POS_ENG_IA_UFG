"""Database connection, session factory, and configuration.

Manages SQLAlchemy engine creation, session management, and connection pooling
with support for SQLite (MVP) and PostgreSQL (production migration path).
"""

import os
from typing import Any, Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Database URL from environment or default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/countries.db")

# Connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"

# Engine creation with environment-specific settings
engine: Engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration (MVP)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_pre_ping=POOL_PRE_PING,
    )

    # Enable foreign key constraints for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
        """Enable foreign key constraints in SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # PostgreSQL configuration (production)
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=POOL_PRE_PING,
    )

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def init_db() -> None:
    """Initialize database by creating all tables.

    Should be called once at application startup.
    Uses Base.metadata from models.

    Raises:
        Exception: If table creation fails.
    """
    try:
        from app.database.models import Base

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db_session() -> Generator[Session, None, None]:
    """Dependency injection for database sessions.

    Yields:
        SQLAlchemy Session instance

    Usage in FastAPI:
        @app.get("/countries")
        def get_countries(session: Session = Depends(get_db_session)):
            return session.query(Country).all()
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def get_engine() -> Engine:
    """Get the SQLAlchemy engine instance.

    Returns:
        SQLAlchemy Engine
    """
    return engine


def dispose_db() -> None:
    """Dispose of all connections in the pool.

    Should be called at application shutdown.
    Useful for graceful shutdown and connection cleanup.
    """
    engine.dispose()
    logger.info("Database connections disposed")
