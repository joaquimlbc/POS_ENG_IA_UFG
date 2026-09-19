"""Integration tests for US-008/US-009: persisting ingestion pipeline output.

Priority: CRITICAL
Covers CountryRepository.upsert_with_relations, which persists Country ORM
instances (with Language/Currency/Timezone relationships attached) as
produced by app.api.rest_countries.transform_normalized_countries.
"""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.rest_countries import normalize_countries, transform_normalized_countries
from app.database.models import Base, Country
from app.database.repository import CountryRepository
from app.utils.errors import BatchProcessError

RAW_BRAZIL = {
    "names": {"common": "Brazil", "official": "Federative Republic of Brazil"},
    "codes": {"alpha_2": "BR", "alpha_3": "BRA"},
    "region": "Americas",
    "subregion": "South America",
    "population": 215313498,
    "area": {"kilometers": 8514877.0},
    "coordinates": {"lat": -15.793889, "lng": -47.882778},
    "languages": [{"name": "Portuguese"}],
    "currencies": [{"code": "BRL", "name": "Brazilian real"}],
    "timezones": ["UTC-03:00"],
}

RAW_FRANCE = {
    "names": {"common": "France", "official": "French Republic"},
    "codes": {"alpha_2": "FR", "alpha_3": "FRA"},
    "region": "Europe",
    "population": 67750000,
    "area": {"kilometers": 551695.0},
    "languages": [{"name": "French"}],
    "currencies": [{"code": "EUR", "name": "Euro"}],
    "timezones": ["UTC+01:00"],
}


def _build_countries(raw_data: list[dict]) -> list[Country]:
    normalized, errors = normalize_countries(raw_data)
    assert errors == []
    transformed, transform_errors = transform_normalized_countries(normalized)
    assert transform_errors == []
    return transformed


class TestUpsertWithRelations:
    """Test suite for CountryRepository.upsert_with_relations."""

    def test_insert_new_countries_with_relations(self, session: Session) -> None:
        """Verify new countries are inserted with their languages/currencies/timezones.

        Why: Validates US-008 persistence of ingestion pipeline output,
        including nested relationships built by transform_normalized_countries.
        """
        countries = _build_countries([RAW_BRAZIL, RAW_FRANCE])
        repo = CountryRepository(session)

        total, inserted, updated = repo.upsert_with_relations(countries)

        assert total == 2
        assert inserted == 2
        assert updated == 0

        brazil = repo.get_by_iso2("BR")
        assert brazil is not None
        assert brazil.name_common == "Brazil"
        assert len(brazil.languages) == 1
        assert brazil.languages[0].language_name == "Portuguese"
        assert len(brazil.currencies) == 1
        assert len(brazil.timezones) == 1

    def test_upsert_updates_existing_country_and_replaces_relations(
        self, session: Session
    ) -> None:
        """Verify re-running ingestion updates fields and replaces relationships.

        Why: Ingestion must be idempotent; re-syncing the same country should
        not create duplicate rows nor leak stale related rows.
        """
        repo = CountryRepository(session)
        repo.upsert_with_relations(_build_countries([RAW_BRAZIL]))

        updated_raw = dict(RAW_BRAZIL)
        updated_raw["population"] = 220000000
        updated_raw["languages"] = [{"name": "Portuguese"}, {"name": "English"}]

        total, inserted, updated = repo.upsert_with_relations(
            _build_countries([updated_raw])
        )

        assert total == 1
        assert inserted == 0
        assert updated == 1

        brazil = repo.get_by_iso2("BR")
        assert brazil.population == 220000000
        assert len(brazil.languages) == 2
        assert repo.count_all() == 1

    def test_upsert_mixed_insert_and_update(self, session: Session) -> None:
        """Verify a batch with one existing and one new country is split correctly."""
        repo = CountryRepository(session)
        repo.upsert_with_relations(_build_countries([RAW_BRAZIL]))

        total, inserted, updated = repo.upsert_with_relations(
            _build_countries([RAW_BRAZIL, RAW_FRANCE])
        )

        assert total == 2
        assert inserted == 1  # France
        assert updated == 1  # Brazil
        assert repo.count_all() == 2

    def test_upsert_empty_list(self, session: Session) -> None:
        """Verify an empty batch is a no-op that reports zero counts."""
        repo = CountryRepository(session)

        total, inserted, updated = repo.upsert_with_relations([])

        assert (total, inserted, updated) == (0, 0, 0)
        assert repo.count_all() == 0

    def test_per_item_failure_is_counted_and_reported(self, session: Session) -> None:
        """Verify one bad item in a batch fails without losing the good ones.

        Why: Covers the per-item exception handler - a poisoned lookup for
        the second country must not abort processing of the first.
        """
        countries = _build_countries([RAW_BRAZIL, RAW_FRANCE])
        repo = CountryRepository(session)
        real_query = session.query
        calls = {"n": 0}

        def flaky_query(*args: object, **kwargs: object) -> object:
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("simulated lookup failure")
            return real_query(*args, **kwargs)

        with patch.object(session, "query", side_effect=flaky_query):
            with pytest.raises(BatchProcessError) as exc_info:
                repo.upsert_with_relations(countries)

        assert exc_info.value.successful == 1
        assert exc_info.value.failed == 1
        assert exc_info.value.errors[0]["country"] == "France"

    def test_unexpected_commit_failure_is_wrapped_in_batch_error(self) -> None:
        """Verify a failure at commit time (not per-item) rolls back and wraps.

        Why: Distinct from the per-item failure path - this is the outer
        `except Exception` around the whole batch, triggered by something
        that isn't caught earlier (e.g. the DB connection dropping at
        commit time). Uses its own standalone engine/session rather than
        the shared fixtures, since this test intentionally triggers a real
        `session.rollback()` and a session sharing a fixture's externally
        managed transaction would leave that transaction inconsistent
        afterwards.
        """
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(engine)
        db_session = sessionmaker(bind=engine)()

        try:
            countries = _build_countries([RAW_BRAZIL])
            repo = CountryRepository(db_session)

            with patch.object(
                db_session, "commit", side_effect=RuntimeError("connection lost")
            ):
                with pytest.raises(BatchProcessError) as exc_info:
                    repo.upsert_with_relations(countries)

            assert exc_info.value.failed == 1
            assert "connection lost" in exc_info.value.errors[0]["error"]
        finally:
            db_session.close()
            engine.dispose()
