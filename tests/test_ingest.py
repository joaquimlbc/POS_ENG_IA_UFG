"""Tests for the end-to-end ingestion script (US-009).

Priority: HIGH
Verifies app.scripts.ingest.ingest_countries orchestrates fetch -> normalize
-> transform -> persist correctly and produces an accurate report.
"""

from unittest.mock import patch

from sqlalchemy.orm import Session

from app.scripts.ingest import ingest_countries, main
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

RAW_INVALID = {
    # Missing required fields (codes.alpha_3, region, population) -> normalization error
    "names": {"common": "Broken", "official": "Broken Land"},
    "codes": {"alpha_2": "XX"},
}


class TestIngestCountries:
    """Test suite for the full ingestion pipeline orchestration."""

    def test_ingest_fetches_normalizes_transforms_and_persists(
        self, session: Session
    ) -> None:
        """Verify a successful run reports counts and persists data.

        Why: Validates the orchestration described by US-009 end to end,
        using a real (in-memory) database session.
        """
        with patch(
            "app.scripts.ingest.fetch_countries",
            return_value=[RAW_BRAZIL, RAW_FRANCE],
        ):
            report = ingest_countries(session=session)

        assert report.status == "success"
        assert report.fetched == 2
        assert report.normalized == 2
        assert report.transformed == 2
        assert report.inserted == 2
        assert report.updated == 0
        assert report.failed == 0
        assert report.duration_seconds >= 0

    def test_ingest_is_idempotent_on_rerun(self, session: Session) -> None:
        """Verify running ingestion twice upserts rather than duplicating.

        Why: The scheduler (US-012) will call this repeatedly; re-ingesting
        must never create duplicate country rows.
        """
        with patch(
            "app.scripts.ingest.fetch_countries",
            return_value=[RAW_BRAZIL],
        ):
            ingest_countries(session=session)
            report = ingest_countries(session=session)

        assert report.status == "success"
        assert report.inserted == 0
        assert report.updated == 1

    def test_ingest_reports_partial_failure_on_normalization_errors(
        self, session: Session
    ) -> None:
        """Verify malformed records are skipped and reflected in the report.

        Why: The REST Countries API can return incomplete records; ingestion
        must continue processing valid ones and surface the failures.
        """
        with patch(
            "app.scripts.ingest.fetch_countries",
            return_value=[RAW_BRAZIL, RAW_INVALID],
        ):
            report = ingest_countries(session=session)

        assert report.fetched == 2
        assert report.normalized == 1
        assert report.status == "partial_failure"
        assert len(report.normalization_errors) == 1
        assert report.inserted == 1

    def test_ingest_propagates_fetch_failures(self, session: Session) -> None:
        """Verify a fetch-stage exception aborts the run and is re-raised.

        Why: Callers (CLI, scheduler) need a hard failure signal when the
        upstream API is unreachable, rather than a silently empty report.
        """
        import requests

        with patch(
            "app.scripts.ingest.fetch_countries",
            side_effect=requests.RequestException("boom"),
        ):
            try:
                ingest_countries(session=session)
                assert False, "expected RequestException to propagate"
            except requests.RequestException:
                pass

    def test_ingest_reports_partial_failure_on_persistence_errors(
        self, session: Session
    ) -> None:
        """Verify persistence-layer failures are surfaced without crashing the run.

        Why: A single bad row (e.g. a constraint violation) must not lose the
        report for the rest of a large batch.
        """
        with patch(
            "app.scripts.ingest.fetch_countries",
            return_value=[RAW_BRAZIL, RAW_FRANCE],
        ), patch(
            "app.database.repository.CountryRepository.upsert_with_relations",
            side_effect=BatchProcessError(
                total=2, successful=1, failed=1, errors=[{"error": "boom"}]
            ),
        ):
            report = ingest_countries(session=session)

        assert report.status == "partial_failure"
        assert report.inserted == 1
        assert report.failed == 1

    def test_ingest_creates_and_closes_own_session_when_none_provided(self) -> None:
        """Verify the script manages its own session lifecycle when run standalone.

        Why: The CLI entry point calls ingest_countries() without a session;
        it must open and close one itself rather than leaking connections.
        """
        with patch(
            "app.scripts.ingest.fetch_countries",
            return_value=[RAW_BRAZIL],
        ):
            with patch("app.scripts.ingest.SessionLocal") as mock_session_factory:
                fake_session = mock_session_factory.return_value
                fake_session.query.return_value.filter.return_value.all.return_value = (
                    []
                )

                report = ingest_countries()

        assert report.status == "success"
        fake_session.close.assert_called_once()


class TestIngestCli:
    """Test suite for the `python -m app.scripts.ingest` CLI entry point."""

    def test_main_returns_zero_on_success(self, capsys) -> None:
        """Verify main() prints the report and exits 0 on a successful run."""
        with patch("app.scripts.ingest.init_db"), patch(
            "app.scripts.ingest.ingest_countries"
        ) as mock_ingest:
            from app.scripts.ingest import IngestReport
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            mock_ingest.return_value = IngestReport(
                started_at=now,
                completed_at=now,
                fetched=2,
                inserted=2,
                status="success",
                message="Ingested 2/2 countries",
            )

            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Status: success" in captured.out

    def test_main_returns_one_on_exception(self) -> None:
        """Verify main() exits 1 when the pipeline raises (e.g. API unreachable)."""
        with patch("app.scripts.ingest.init_db"), patch(
            "app.scripts.ingest.ingest_countries", side_effect=RuntimeError("down")
        ):
            exit_code = main()

        assert exit_code == 1
