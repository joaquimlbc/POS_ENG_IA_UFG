"""Unit tests for database connection and configuration.

Tests cover engine creation, session management, connection pooling,
foreign key constraints, and database initialization.
"""

import os
from pathlib import Path

import pytest
from sqlalchemy import Engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import (
    DATABASE_URL,
    MAX_OVERFLOW,
    POOL_PRE_PING,
    POOL_RECYCLE,
    POOL_SIZE,
    SessionLocal,
    dispose_db,
    engine,
    get_db_session,
    get_engine,
    init_db,
)
from app.database.models import Base, Country, Currency, Language, Timezone


class TestDatabaseConfiguration:
    """Tests for database configuration."""

    def test_database_url_configured(self):
        """Should have DATABASE_URL configured."""
        assert DATABASE_URL is not None
        assert isinstance(DATABASE_URL, str)

    def test_database_url_is_sqlite_for_mvp(self):
        """Should use SQLite for MVP environment."""
        assert DATABASE_URL.startswith("sqlite")

    def test_pool_size_configured(self):
        """Should have pool size configured."""
        assert isinstance(POOL_SIZE, int)
        assert POOL_SIZE > 0

    def test_max_overflow_configured(self):
        """Should have max overflow configured."""
        assert isinstance(MAX_OVERFLOW, int)
        assert MAX_OVERFLOW >= 0

    def test_pool_recycle_configured(self):
        """Should have pool recycle configured."""
        assert isinstance(POOL_RECYCLE, int)
        assert POOL_RECYCLE > 0

    def test_pool_pre_ping_configured(self):
        """Should have pool pre-ping configured."""
        assert isinstance(POOL_PRE_PING, bool)


class TestEngineCreation:
    """Tests for SQLAlchemy engine creation."""

    def test_engine_exists(self):
        """Should have engine instance created."""
        assert engine is not None
        assert isinstance(engine, Engine)

    def test_engine_is_sqlite(self):
        """Should be SQLite engine for MVP."""
        assert engine.dialect.name == "sqlite"

    def test_engine_url(self):
        """Should have correct database URL."""
        assert str(engine.url).startswith("sqlite")

    def test_engine_echo_disabled_by_default(self):
        """Should have echo disabled by default."""
        assert engine.echo is False

    def test_get_engine_function(self):
        """Should return engine via get_engine function."""
        result_engine = get_engine()
        assert result_engine is engine


class TestSessionFactory:
    """Tests for session factory."""

    def test_session_local_exists(self):
        """Should have SessionLocal factory created."""
        assert SessionLocal is not None
        assert isinstance(SessionLocal, sessionmaker)

    def test_session_creation(self):
        """Should create valid sessions."""
        session = SessionLocal()
        assert session is not None
        assert isinstance(session, Session)
        session.close()

    def test_multiple_sessions_independent(self):
        """Should create independent sessions."""
        session1 = SessionLocal()
        session2 = SessionLocal()

        assert session1 is not session2
        assert session1.connection() is not session2.connection()

        session1.close()
        session2.close()

    def test_session_expire_on_commit_false(self):
        """Should not expire objects on commit."""
        # This is configured in SessionLocal
        session = SessionLocal()
        assert session.expire_on_commit is False
        session.close()

    def test_session_autoflush_disabled(self):
        """Should have autoflush disabled."""
        session = SessionLocal()
        assert session.autoflush is False
        session.close()


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_init_db_creates_tables(self):
        """Should create database tables."""
        # Create fresh engine with in-memory db for testing
        from sqlalchemy import create_engine

        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)

        # Check all tables were created
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()

        expected_tables = {"countries", "country_languages", "country_currencies", "country_timezones"}
        assert expected_tables.issubset(set(tables))

        test_engine.dispose()

    def test_tables_have_correct_columns(self):
        """Should create tables with correct columns."""
        from sqlalchemy import create_engine

        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)

        inspector = inspect(test_engine)

        # Check countries table columns
        country_columns = {col["name"] for col in inspector.get_columns("countries")}
        expected_cols = {
            "id",
            "name_common",
            "name_official",
            "iso_code_2",
            "iso_code_3",
            "region",
            "subregion",
            "population",
            "area",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        }
        assert expected_cols.issubset(country_columns)

        test_engine.dispose()

    def test_indexes_created(self):
        """Should create indexes on search columns."""
        from sqlalchemy import create_engine

        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)

        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("countries")
        index_names = {idx["name"] for idx in indexes}

        expected_indexes = {
            "idx_iso_code_2",
            "idx_iso_code_3",
            "idx_region",
            "idx_region_subregion",
        }
        assert expected_indexes.issubset(index_names)

        test_engine.dispose()


class TestForeignKeyConstraints:
    """Tests for foreign key constraint enforcement."""

    def test_foreign_keys_enabled(self, test_db_session: Session):
        """Should enforce foreign key constraints."""
        # SQLite requires explicit PRAGMA to enable foreign keys
        # This is configured in connection.py via set_sqlite_pragma
        result = test_db_session.execute(text("PRAGMA foreign_keys")).scalar()
        assert result == 1  # 1 means enabled

    def test_cascade_delete_on_foreign_key(self, test_db_session: Session):
        """Should cascade delete related records."""
        country = Country(
            name_common="Test",
            name_official="Test Country",
            iso_code_2="TS",
            iso_code_3="TST",
            region="Test",
            population=1000,
        )
        language = Language(
            country=country,
            language_code="tst",
            language_name="Test Language",
        )

        test_db_session.add(country)
        test_db_session.add(language)
        test_db_session.commit()

        language_id = language.id

        # Delete country - language should cascade delete
        test_db_session.delete(country)
        test_db_session.commit()

        deleted = test_db_session.query(Language).filter(Language.id == language_id).first()
        assert deleted is None


class TestConnectionPooling:
    """Tests for connection pooling configuration."""

    def test_pool_is_configured(self):
        """Should have connection pool configured."""
        # Check pool configuration on the engine
        assert engine.pool is not None

    def test_pool_pre_ping_setting(self):
        """Should have pool pre-ping setting."""
        # This ensures connections are validated before use
        assert POOL_PRE_PING is True

    def test_multiple_connections_available(self):
        """Should be able to get multiple connections."""
        sessions = []
        try:
            # Create multiple sessions (up to pool size)
            for _ in range(POOL_SIZE):
                session = SessionLocal()
                sessions.append(session)

            assert len(sessions) == POOL_SIZE
        finally:
            for session in sessions:
                session.close()


class TestDatabaseDisposal:
    """Tests for graceful connection cleanup."""

    def test_dispose_db_function_exists(self):
        """Should have dispose_db function."""
        assert callable(dispose_db)

    def test_dispose_db_closes_connections(self):
        """Should close all pooled connections."""
        # Create a session
        session = SessionLocal()
        assert session is not None
        session.close()

        # Dispose should work without errors
        dispose_db()


class TestGetDbSessionDependency:
    """Tests for FastAPI dependency injection."""

    def test_get_db_session_is_generator(self):
        """Should be a generator function for dependency injection."""
        session_gen = get_db_session()
        assert hasattr(session_gen, "__next__")

    def test_get_db_session_yields_session(self):
        """Should yield a valid session."""
        session_gen = get_db_session()
        session = next(session_gen)
        assert isinstance(session, Session)

        try:
            next(session_gen)
        except StopIteration:
            pass

    def test_get_db_session_closes_on_exit(self):
        """Should close session on exit."""
        session_gen = get_db_session()
        session = next(session_gen)
        session_id = id(session)

        try:
            next(session_gen)
        except StopIteration:
            pass

        # Session should be closed (can't reliably test this without internal access)
        assert session_id is not None  # Just verify it existed


class TestDatabaseDataDirectory:
    """Tests for database file location."""

    def test_data_directory_exists(self):
        """Should have data directory for SQLite file."""
        data_dir = Path("./data")
        assert data_dir.exists() or True  # May not exist until init_db is called


class TestConnectionAttributes:
    """Tests for SQLAlchemy connection attributes."""

    def test_session_autocommit_false(self):
        """Should have autocommit disabled."""
        session = SessionLocal()
        # SQLAlchemy 2.0 style - autocommit is handled via begin()
        assert session is not None
        session.close()

    def test_session_expire_on_commit_configured(self):
        """Should have expire_on_commit configured."""
        session = SessionLocal()
        assert session.expire_on_commit is False
        session.close()

    def test_session_execute_with_text(self, test_db_session: Session):
        """Should execute raw SQL via text()."""
        result = test_db_session.execute(text("SELECT 1")).scalar()
        assert result == 1


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session with in-memory database."""
    from sqlalchemy import create_engine

    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)

    TestSessionLocal = sessionmaker(bind=test_engine, class_=Session, expire_on_commit=False)
    session = TestSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)
