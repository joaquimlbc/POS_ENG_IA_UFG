"""Tests for CountryRepository/StatisticsRepository error and edge paths.

Priority: ALTO
Closes coverage gaps left by the CRUD happy-path tests elsewhere
(test_country_crud.py, test_sync.py): direct repository-level not-found
paths, IntegrityError translation, region-scoped queries, and the
upsert_batch (CountryCreate-based) failure branches - the sibling of
upsert_with_relations, covered separately in test_ingest_persistence.py.
"""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base
from app.database.repository import CountryRepository, StatisticsRepository
from app.models.task import CountryCreate, CountryUpdate
from app.utils.errors import (
    BatchProcessError,
    DuplicateRecordError,
    IntegrityError,
    RecordNotFoundError,
    TransactionError,
)


def _country_payload(**overrides: object) -> CountryCreate:
    defaults = dict(
        name_common="Brazil",
        name_official="Federative Republic of Brazil",
        iso_code_2="BR",
        iso_code_3="BRA",
        region="Americas",
        population=215313498,
    )
    defaults.update(overrides)
    return CountryCreate(**defaults)


def _standalone_session() -> Session:
    """A fully self-contained in-memory session (own commit/rollback lifecycle).

    Used whenever a test forces a real `session.rollback()` inside the
    repository code under test: a session sharing a fixture's externally
    managed transaction would leave that transaction inconsistent
    afterwards (see the same note in test_ingest_persistence.py).
    """
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class TestCreateErrorPaths:
    """Tests for CountryRepository.create's exception-translation branches."""

    def test_duplicate_iso_code_raises_duplicate_record_error(self) -> None:
        """Verify a UNIQUE constraint violation on create() maps to DuplicateRecordError."""
        session = _standalone_session()
        try:
            repo = CountryRepository(session)
            repo.create(_country_payload())

            with pytest.raises(DuplicateRecordError):
                repo.create(_country_payload(name_official="Different Official Name"))
        finally:
            session.close()

    def test_non_unique_integrity_error_is_wrapped(self) -> None:
        """Verify a non-UNIQUE integrity failure maps to the generic IntegrityError.

        Why: create() special-cases UNIQUE violations (DuplicateRecordError);
        any other integrity failure (e.g. a NOT NULL violation surfaced at
        the DB layer) must still be caught and translated, not leak a raw
        SQLAlchemy exception to callers.
        """
        session = _standalone_session()
        try:
            repo = CountryRepository(session)
            with patch.object(
                session,
                "commit",
                side_effect=SQLAlchemyIntegrityError(
                    "NOT NULL constraint failed: countries.population", None, None
                ),
            ):
                with pytest.raises(IntegrityError):
                    repo.create(_country_payload())
        finally:
            session.close()


class TestUpdateErrorPaths:
    """Tests for CountryRepository.update's not-found and integrity branches."""

    def test_update_nonexistent_country_raises_not_found(
        self, session: Session
    ) -> None:
        """Verify updating a nonexistent country raises RecordNotFoundError directly
        from the repository (not just from the service layer's own pre-check)."""
        repo = CountryRepository(session)

        with pytest.raises(RecordNotFoundError):
            repo.update(999_999, CountryUpdate(population=1))

    def test_update_integrity_failure_is_wrapped(self) -> None:
        """Verify a commit failure during update() is translated to IntegrityError."""
        session = _standalone_session()
        try:
            repo = CountryRepository(session)
            country = repo.create(_country_payload())

            with patch.object(
                session,
                "commit",
                side_effect=SQLAlchemyIntegrityError("constraint failed", None, None),
            ):
                with pytest.raises(IntegrityError):
                    repo.update(country.id, CountryUpdate(population=999))
        finally:
            session.close()


class TestDeleteErrorPaths:
    """Tests for CountryRepository.delete's not-found and integrity branches."""

    def test_delete_nonexistent_country_returns_false(self, session: Session) -> None:
        """Verify deleting a nonexistent country returns False rather than raising."""
        repo = CountryRepository(session)

        assert repo.delete(999_999) is False

    def test_delete_integrity_failure_is_wrapped_as_transaction_error(self) -> None:
        """Verify a commit failure during delete() is translated to TransactionError."""
        session = _standalone_session()
        try:
            repo = CountryRepository(session)
            country = repo.create(_country_payload())

            with patch.object(
                session,
                "commit",
                side_effect=SQLAlchemyIntegrityError("constraint failed", None, None),
            ):
                with pytest.raises(TransactionError):
                    repo.delete(country.id)
        finally:
            session.close()


class TestRegionScopedQueries:
    """Tests for get_by_region and count_by_region."""

    def test_get_by_region_returns_only_matching_countries(
        self, session: Session
    ) -> None:
        """Verify get_by_region filters correctly and excludes other regions."""
        repo = CountryRepository(session)
        repo.create(_country_payload())  # Americas
        repo.create(
            _country_payload(
                name_common="France",
                name_official="French Republic",
                iso_code_2="FR",
                iso_code_3="FRA",
                region="Europe",
            )
        )

        americas = repo.get_by_region("Americas")

        assert len(americas) == 1
        assert americas[0].name_common == "Brazil"

    def test_get_by_region_empty_when_no_match(self, session: Session) -> None:
        """Verify get_by_region returns an empty list for an unrepresented region."""
        repo = CountryRepository(session)
        repo.create(_country_payload())

        assert repo.get_by_region("Oceania") == []

    def test_count_by_region_aggregates_correctly(self, session: Session) -> None:
        """Verify count_by_region groups and counts countries per region."""
        repo = CountryRepository(session)
        repo.create(_country_payload())
        repo.create(
            _country_payload(
                name_common="France",
                name_official="French Republic",
                iso_code_2="FR",
                iso_code_3="FRA",
                region="Europe",
            )
        )
        repo.create(
            _country_payload(
                name_common="Germany",
                name_official="Federal Republic of Germany",
                iso_code_2="DE",
                iso_code_3="DEU",
                region="Europe",
            )
        )

        counts = repo.count_by_region()

        assert counts == {"Americas": 1, "Europe": 2}

    def test_count_by_region_empty_database(self, session: Session) -> None:
        """Verify count_by_region returns an empty dict when there is no data."""
        repo = CountryRepository(session)

        assert repo.count_by_region() == {}


class TestUpsertBatchErrorPaths:
    """Tests for the CountryCreate-based upsert_batch's failure branches.

    Sibling of upsert_with_relations (tested in test_ingest_persistence.py);
    used by CountryService.sync_countries_batch rather than the ingestion
    pipeline.
    """

    def test_per_item_failure_is_counted_and_reported(self, session: Session) -> None:
        """Verify one bad item in a batch fails without losing the good ones."""
        repo = CountryRepository(session)
        countries = [
            _country_payload(),
            _country_payload(
                name_common="France",
                name_official="French Republic",
                iso_code_2="FR",
                iso_code_3="FRA",
                region="Europe",
            ),
        ]
        real_query = session.query
        calls = {"n": 0}

        def flaky_query(*args: object, **kwargs: object) -> object:
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("simulated lookup failure")
            return real_query(*args, **kwargs)

        with patch.object(session, "query", side_effect=flaky_query):
            with pytest.raises(BatchProcessError) as exc_info:
                repo.upsert_batch(countries)

        assert exc_info.value.successful == 1
        assert exc_info.value.failed == 1

    def test_unexpected_commit_failure_is_wrapped_in_batch_error(self) -> None:
        """Verify a commit-time failure (not per-item) rolls back and wraps."""
        session = _standalone_session()
        try:
            repo = CountryRepository(session)

            with patch.object(
                session, "commit", side_effect=RuntimeError("connection lost")
            ):
                with pytest.raises(BatchProcessError) as exc_info:
                    repo.upsert_batch([_country_payload()])

            assert exc_info.value.failed == 1
            assert "connection lost" in exc_info.value.errors[0]["error"]
        finally:
            session.close()


class TestStatisticsRepositoryEdgeCases:
    """Edge cases for StatisticsRepository not covered by the happy-path tests."""

    def test_global_stats_on_empty_database(self, session: Session) -> None:
        """Verify global stats degrade to zeros rather than raising on empty data."""
        stats_repo = StatisticsRepository(session)

        result = stats_repo.get_global_stats()

        assert result["total_countries"] == 0
        assert result["total_population"] == 0
        assert result["average_population"] == 0.0
        assert result["average_area"] == 0.0
